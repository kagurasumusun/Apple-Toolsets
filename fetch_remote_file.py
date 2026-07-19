import paramiko
import time
import re
import base64

def get_file_content(filepath):
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
    
    # We will run a python script on the remote that reads the file,
    # base64 encodes it, and prints it with clear boundary markers.
    remote_py = f"""import base64, sys
try:
    with open('{filepath}', 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('utf-8')
    print('@@@START_FILE@@@' + b64 + '@@@END_FILE@@@')
except Exception as e:
    print('@@@START_FILE@@@ERROR:' + str(e) + '@@@END_FILE@@@')
"""
    cmd = f"python3 -c \"{remote_py}\"\n"
    shell.send(cmd)
    
    out_total = ""
    for _ in range(20):
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if '@@@END_FILE@@@' in out_total:
                break
                
    client.close()

    try:
        # Extract between markers
        start_idx = out_total.find('@@@START_FILE@@@')
        end_idx = out_total.find('@@@END_FILE@@@')
        if start_idx != -1 and end_idx != -1:
            data_str = out_total[start_idx + 16:end_idx]
            # remove line breaks, carriage returns from tmux
            data_str = re.sub(r'[\r\n\s]', '', data_str)
            if data_str.startswith('ERROR:'):
                print(f"Remote error: {data_str}")
                return None
            
            return base64.b64decode(data_str)
        else:
            print("Could not find markers. Raw output:")
            print(out_total)
    except Exception as e:
        print("Error decoding:", e)
        print("Raw output:", out_total)

if __name__ == "__main__":
    log_data = get_file_content('/Users/runner/run.log')
    if log_data:
        with open("/home/user/run.log", "wb") as f:
            f.write(log_data)
        print("Wrote log to /home/user/run.log")
        print(log_data.decode('utf-8')[-2000:])
