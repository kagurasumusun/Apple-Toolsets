import paramiko
import sys
import time
import re

def clean_tmux_output(output):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean = ansi_escape.sub('', output)
    clean = clean.replace('[K', '').replace('\x0f', '').replace('\x07', '')
    clean = re.sub(r'\n\s*\n', '\n', clean)
    return clean

def run_upterm_test():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        key = paramiko.Ed25519Key.from_private_key_file(key_path)
        client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
        
        shell = client.invoke_shell(term='vt100', width=200, height=50)
        time.sleep(2)
        
        if shell.recv_ready():
            shell.recv(65535) # Clear initial buffer
            
        print("Executing script on Mac...")
        cmd = "cd /Users/runner/work/Apple-actool-py/Apple-actool-py && ls -la out_test_mac && cat result.json | head -n 20\n"
        shell.send(cmd)
        
        time.sleep(5)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        print("=== Raw Output ===")
        print(clean_tmux_output(output))
        
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
