import paramiko
import time
import base64
import re

def read_log():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(key_path)
    client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
    
    shell = client.invoke_shell(term='vt100', width=200, height=50)
    time.sleep(2)
    if shell.recv_ready(): shell.recv(65535)
    
    # We will delimit the output
    shell.send("echo '---START_B64---' && base64 /tmp/run.log && echo '---END_B64---'\n")
    
    out_total = ""
    for _ in range(10):
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if '---END_B64---' in out_total:
                break
    
    client.close()

    try:
        # Extract base64 part
        start_idx = out_total.find('---START_B64---')
        end_idx = out_total.find('---END_B64---', start_idx)
        if start_idx != -1 and end_idx != -1:
            b64_data = out_total[start_idx + len('---START_B64---'):end_idx]
            
            # Clean up base64 string
            b64_data = re.sub(r'[^A-Za-z0-9+/=]', '', b64_data)
            
            log_data = base64.b64decode(b64_data).decode('utf-8')
            print("=== DECODED LOG ===")
            print(log_data)
            print("===================")
        else:
            print("Could not find markers. Raw output:")
            print(out_total)
    except Exception as e:
        print("Error decoding:", e)
        print("Raw output:", out_total)

if __name__ == "__main__":
    read_log()
