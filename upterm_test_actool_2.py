import paramiko
import sys
import time
import re

def run_upterm_test():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    # 接続のセットアップ
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        key = paramiko.Ed25519Key.from_private_key_file(key_path)
        client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
        
        # ptyを強制的に使ってインタラクティブシェルを開く
        shell = client.invoke_shell(term='xterm', width=132, height=43)
        time.sleep(2)
        
        # バッファクリア
        if shell.recv_ready():
            shell.recv(65535)
            
        print("--- Sending commands without tmux interference ---")
        
        # tmuxの内側なので、bashを新しく立ち上げてクリーンな出力を得る
        shell.send("bash --norc\\n")
        time.sleep(1)
        if shell.recv_ready(): shell.recv(65535)
        
        commands = [
            "cd /Users/runner/work/Apple-actool-py/Apple-actool-py",
            "git fetch origin fix-bugs",
            "git checkout fix-bugs",
            "git pull origin fix-bugs",
            "export PYTHONPATH=.",
            "rm -rf out_test_mac",
            "python3 -m actool_linux tests/test_data/test.xcassets --compile out_test_mac --platform iphoneos --minimum-deployment-target 15.0",
            "xcrun assetutil -I out_test_mac/Assets.car > out_test_mac/dump.json",
            "head -n 25 out_test_mac/dump.json"
        ]
        
        # 1行ずつ実行して、結果をまとめる
        for cmd in commands:
            shell.send(cmd + "\\n")
            time.sleep(2)
            
        # 最後に一気に読み取る
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        # 制御文字のクリーンアップ (簡易)
        clean_out = re.sub(r'\\x1b\\[[0-9;]*[a-zA-Z]', '', output)
        print(clean_out)
            
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
