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
        
        # コマンドを直接実行 (exec_command は pty なしで実行できるため tmux に邪魔されない)
        commands = [
            "cd /Users/runner/work/Apple-actool-py/Apple-actool-py && git fetch origin fix-bugs && git checkout fix-bugs && git pull origin fix-bugs",
            "cd /Users/runner/work/Apple-actool-py/Apple-actool-py && export PYTHONPATH=. && rm -rf out_test_mac && python3 -m actool_linux tests/test_data/test.xcassets --compile out_test_mac --platform iphoneos --minimum-deployment-target 15.0",
            "cd /Users/runner/work/Apple-actool-py/Apple-actool-py && xcrun assetutil -I out_test_mac/Assets.car > out_test_mac/dump.json",
            "cd /Users/runner/work/Apple-actool-py/Apple-actool-py && head -n 30 out_test_mac/dump.json"
        ]
        
        for cmd in commands:
            print(f"> {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            # コマンドの終了を待つ
            exit_status = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            if out:
                print(out)
            if err:
                print(f"Error output: {err}")
            
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
