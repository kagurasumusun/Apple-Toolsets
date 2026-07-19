import paramiko
import time
import base64

HOST = "uptermd.upterm.dev"
PORT = 22
USERNAME = "NZavJ93kKawd70bya6xE"
KEY_PATH = "/home/user/.ssh/id_ed25519"

def pull_raw():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    client.connect(hostname=HOST, port=PORT, username=USERNAME, pkey=key, look_for_keys=False)
    shell = client.invoke_shell(term='vt100', width=200, height=50)
    time.sleep(2)
    if shell.recv_ready(): shell.recv(65535)
    
    remote_py = '''import sys, base64
try:
    with open("/tmp/cmd.log", "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    sys.stdout.write("@@@PULL_START@@@" + b64 + "@@@PULL_END@@@\\n")
except Exception as e:
    sys.stdout.write("@@@PULL_START@@@ERROR:" + str(e) + "@@@PULL_END@@@\\n")
'''
    b64_py = base64.b64encode(remote_py.encode('utf-8')).decode('utf-8')
    shell.send(f"echo '{b64_py}' | base64 -D > /tmp/read.py\n")
    time.sleep(1)
    shell.send("python3 /tmp/read.py\n")
    
    out_total = ""
    for _ in range(15):
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if "@@@PULL_END@@@" in out_total:
                break
    
    start_idx = out_total.find('@@@PULL_START@@@')
    end_idx = out_total.find('@@@PULL_END@@@')
    if start_idx != -1 and end_idx != -1:
        data_str = out_total[start_idx+16:end_idx]
        print("RAW DATA_STR:", repr(data_str))
    else:
        print("Failed to pull")

if __name__ == "__main__":
    pull_raw()
