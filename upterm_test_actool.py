import paramiko
import sys
import time

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
            
        print("--- Testing Remote Mac compilation ---")
        
        # 1. 安定版 (Stable) のPythonコードをMac側に転送してテストさせるか、
        # あるいは向こうのMacにある `Apple-actool-py` リポジトリを使用する。
        # まずは向こうに私たちの作成した .car ファイルが読めるか `assetutil` を叩く。
        
        commands = [
            "cd /Users/runner/work/Apple-actool-py/Apple-actool-py",
            "pwd",
            "git pull origin fix-bugs || echo 'Git pull failed'",
            "export PYTHONPATH=.",
            "python3 -m actool_linux tests/test_data/test.xcassets --compile out_test_mac --platform iphoneos --minimum-deployment-target 15.0",
            "ls -la out_test_mac/",
            "xcrun assetutil -I out_test_mac/Assets.car > out_test_mac/dump.json",
            "head -n 20 out_test_mac/dump.json"
        ]
        
        for cmd in commands:
            print(f"> {cmd}")
            shell.send(cmd + "\\n")
            time.sleep(2)  # コマンドの完了を待つ
            if shell.recv_ready():
                output = shell.recv(65535).decode('utf-8', errors='replace')
                # tmuxの制御文字を多少クリーンアップ
                clean_out = output.replace('\\033', '').replace('[K', '').replace('[?25h', '')
                print(clean_out)
            
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
