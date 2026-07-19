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
        cmd = """cat << 'INNER_EOF' > run_test.sh
#!/bin/bash
cd /Users/runner/work/Apple-actool-py/Apple-actool-py
git fetch origin fix-bugs
git checkout fix-bugs
git pull origin fix-bugs
export PYTHONPATH=.
rm -rf out_test_mac
python3 -m actool_linux tests/test_data/test.xcassets --compile out_test_mac --platform iphoneos --minimum-deployment-target 15.0
xcrun assetutil -I out_test_mac/Assets.car > result.json
echo "=== MAC ASSETUTIL JSON HEAD ==="
head -n 25 result.json
echo "=== END OF JSON ==="
INNER_EOF
bash run_test.sh
"""
        shell.send(cmd.replace('\n', '\r'))
        
        # 10秒くらい待つ
        for _ in range(10):
            time.sleep(1)
            if shell.recv_ready():
                out = shell.recv(65535).decode('utf-8', errors='ignore')
                if "=== END OF JSON ===" in clean_tmux_output(out):
                    break
        
        # 最終出力を取得
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        print("=== Results from Remote Mac ===")
        lines = clean_tmux_output(output).split('\n')
        # 必要な部分だけを抽出
        recording = False
        for line in lines:
            if "=== MAC ASSETUTIL JSON HEAD ===" in line:
                recording = True
            if recording:
                print(line)
            if "=== END OF JSON ===" in line:
                break
        
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
