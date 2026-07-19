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
            
        print("Executing script on Mac (Training & ASTC Evaluation)...")
        cmd = """cat << 'INNER_EOF' > run_test.sh
#!/bin/bash
cd /Users/runner/work/Apple-actool-py/Apple-actool-py
git fetch origin fix-bugs
git checkout fix-bugs
git pull origin fix-bugs
export PYTHONPATH=.

# 1. Mac上でのモデルトレーニング実行 (PyTorch/Sklearn不使用、純粋なNumPyで超学習)
echo "=== MAC TRAINING PHASE ==="
python3 scripts/train_micro_ai.py

# 2. ASTCオプティマイザのテスト (独自手法のモック)
echo "=== ASTC OPTIMIZER TEST ==="
cat << 'PY_EOF' > test_astc.py
from actool_linux.nextgen.astc_optimizer import ASTCOptimizer
import numpy as np
data = np.zeros((256, 256, 4), dtype=np.uint8).tobytes()
opt = ASTCOptimizer("8x8")
encoded = opt.encode(data, 256, 256)
print(f"ASTC Encoded Size (8x8): {len(encoded)} bytes")
PY_EOF
python3 test_astc.py

# 3. NextGen Compilerを使って .car を生成し、assetutil で読めるかテスト
echo "=== CAR GENERATION & ASSETUTIL TEST ==="
rm -rf out_nextgen
mkdir -p out_nextgen
python3 -m actool_linux tests/test_data/test.xcassets --compile out_nextgen --platform iphoneos --minimum-deployment-target 15.0 --optimize smart
xcrun assetutil -I out_nextgen/Assets.car > result_nextgen.json
echo "=== MAC ASSETUTIL JSON HEAD ==="
head -n 25 result_nextgen.json
echo "=== END OF JSON ==="
INNER_EOF
bash run_test.sh
"""
        shell.send(cmd.replace('\n', '\r'))
        
        # 結果を待つ
        for _ in range(20):
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
        
        recording = False
        for line in lines:
            if "=== MAC TRAINING PHASE ===" in line or "=== MAC ASSETUTIL JSON HEAD ===" in line or "=== ASTC OPTIMIZER TEST ===" in line:
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
