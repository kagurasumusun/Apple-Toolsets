import paramiko
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
        if shell.recv_ready(): shell.recv(65535)
            
        print("Executing NextGen compiler on Mac...")
        cmd = """cat << 'INNER_EOF' > run_test.sh
#!/bin/bash
cd /Users/runner/work/Apple-actool-py/Apple-actool-py
git fetch origin fix-bugs
git checkout fix-bugs
git pull origin fix-bugs
export PYTHONPATH=.
rm -rf out_nextgen
mkdir -p out_nextgen
# NextGenのモジュールを実行させる
python3 -m actool_linux.nextgen tests/test_data/test.xcassets --compile out_nextgen --platform iphoneos --minimum-deployment-target 15.0 --optimize smart
xcrun assetutil -I out_nextgen/Assets.car > result_nextgen.json
echo "=== MAC ASSETUTIL JSON HEAD ==="
head -n 30 result_nextgen.json
echo "=== END OF JSON ==="
INNER_EOF
bash run_test.sh
"""
        shell.send(cmd.replace('\n', '\r'))
        
        for _ in range(15):
            time.sleep(1)
            if shell.recv_ready():
                out = shell.recv(65535).decode('utf-8', errors='ignore')
                if "=== END OF JSON ===" in out:
                    break
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_out = ansi_escape.sub('', output).replace('[K', '').replace('\x0f', '').replace('\x07', '')
        
        recording = False
        print("=== Results from Remote Mac ===")
        for line in clean_out.split('\n'):
            if "=== MAC ASSETUTIL JSON HEAD ===" in line:
                recording = True
            if recording:
                print(line)
            if "=== END OF JSON ===" in line:
                break
                
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
