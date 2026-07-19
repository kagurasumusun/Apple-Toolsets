import paramiko
import time
import base64
import re
import os

HOST = "uptermd.upterm.dev"
PORT = 22
USERNAME = "NZavJ93kKawd70bya6xE"
KEY_PATH = "/home/user/.ssh/id_ed25519"

def get_shell():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    client.connect(hostname=HOST, port=PORT, username=USERNAME, pkey=key, look_for_keys=False)
    shell = client.invoke_shell(term='vt100', width=200, height=50)
    time.sleep(2)
    if shell.recv_ready(): shell.recv(65535)
    return client, shell

def run_command(shell, cmd, timeout=120):
    b64_cmd = base64.b64encode(cmd.encode('utf-8')).decode('utf-8')
    shell.send("rm -f /tmp/cmd.done /tmp/cmd.log\n")
    time.sleep(0.5)
    wrapper = f"echo '{b64_cmd}' | base64 -D > /tmp/cmd.sh && bash /tmp/cmd.sh > /tmp/cmd.log 2>&1 ; echo DONE > /tmp/cmd.done\n"
    shell.send(wrapper)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        shell.send("cat /tmp/cmd.done 2>/dev/null\n")
        time.sleep(2)
        if shell.recv_ready():
            out = shell.recv(65535).decode('utf-8', errors='ignore')
            if 'DONE' in out:
                break
                
    remote_py = '''import base64
try:
    with open('/tmp/cmd.log', 'rb') as f: data = f.read()
    print("@@@LOG_START@@@" + base64.b64encode(data).decode('utf-8') + "@@@LOG_END@@@")
except Exception as e:
    print("@@@LOG_START@@@ERROR:" + str(e) + "@@@LOG_END@@@")
'''
    shell.send(f"python3 -c \"{remote_py}\"\n")
    
    out_total = ""
    start_time = time.time()
    while time.time() - start_time < 30:
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if "@@@LOG_END@@@" in out_total:
                break
                
    start_idx = out_total.find('@@@LOG_START@@@')
    end_idx = out_total.find('@@@LOG_END@@@')
    if start_idx != -1 and end_idx != -1:
        data_str = out_total[start_idx+15:end_idx]
        data_str = re.sub(r'[^A-Za-z0-9+/=]', '', data_str)
        if data_str.startswith("ERROR:"):
            return data_str
        # Fix padding
        data_str += "=" * ((4 - len(data_str) % 4) % 4)
        return base64.b64decode(data_str).decode('utf-8', errors='replace')
    return "Failed to extract log: " + out_total

def push_file(shell, local_path, remote_path):
    with open(local_path, 'rb') as f:
        data = f.read()
    chunk_size = 50 * 1024
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    shell.send(f"rm -f {remote_path}.b64\n")
    time.sleep(0.5)
    
    for i, chunk in enumerate(chunks):
        b64_chunk = base64.b64encode(chunk).decode('utf-8')
        remote_py = f'''import base64
with open("{remote_path}.b64", "ab") as f:
    f.write(b"{b64_chunk}")
print("@@@CHUNK_{i}_DONE@@@")
'''
        shell.send(f"python3 -c '{remote_py}'\n")
        
        while True:
            time.sleep(0.5)
            if shell.recv_ready():
                out = shell.recv(65535).decode('utf-8', errors='ignore')
                if f"@@@CHUNK_{i}_DONE@@@" in out:
                    break

    shell.send(f"base64 -D -i {remote_path}.b64 -o {remote_path} && echo @@@PUSH_DONE@@@\n")
    for _ in range(10):
        time.sleep(1)
        if shell.recv_ready():
            out = shell.recv(65535).decode('utf-8', errors='ignore')
            if "@@@PUSH_DONE@@@" in out:
                print(f"Pushed {local_path} to {remote_path}")
                return True
    return False

def pull_file(shell, remote_path, local_path):
    shell.send(f"base64 -i {remote_path} -o {remote_path}.b64 && echo @@@B64_DONE@@@\n")
    time.sleep(1)
    
    remote_py = f'''import sys
try:
    with open("{remote_path}.b64", "r") as f: data = f.read()
    print("@@@PULL_START@@@" + data.replace("\\n", "") + "@@@PULL_END@@@")
except Exception as e:
    print("@@@PULL_START@@@ERROR:" + str(e) + "@@@PULL_END@@@")
'''
    shell.send(f"python3 -c '{remote_py}'\n")
    out_total = ""
    for _ in range(60):
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if "@@@PULL_END@@@" in out_total:
                break
    
    start_idx = out_total.find('@@@PULL_START@@@')
    end_idx = out_total.find('@@@PULL_END@@@')
    if start_idx != -1 and end_idx != -1:
        data_str = out_total[start_idx+16:end_idx]
        data_str = re.sub(r'[^A-Za-z0-9+/=]', '', data_str)
        if data_str.startswith("ERROR:"):
            print("Remote error:", data_str)
            return False
        data_str += "=" * ((4 - len(data_str) % 4) % 4)
        with open(local_path, "wb") as f:
            f.write(base64.b64decode(data_str))
        print(f"Pulled {remote_path} to {local_path}")
        return True
    return False

if __name__ == "__main__":
    client, shell = get_shell()
    log = run_command(shell, "ls -la /Users/runner/work")
    print("LOG:")
    print(log)
    client.close()
