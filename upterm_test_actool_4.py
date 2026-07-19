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
        
        # PTY を要求して exec_command を実行
        cmd = """
        cd /Users/runner/work/Apple-actool-py/Apple-actool-py
        git fetch origin fix-bugs
        git checkout fix-bugs
        git pull origin fix-bugs
        export PYTHONPATH=.
        rm -rf out_test_mac
        python3 -m actool_linux tests/test_data/test.xcassets --compile out_test_mac --platform iphoneos --minimum-deployment-target 15.0
        xcrun assetutil -I out_test_mac/Assets.car > out_test_mac/dump.json
        head -n 25 out_test_mac/dump.json
        """
        
        stdin, stdout, stderr = client.exec_command("bash -c '" + cmd.replace('\\n', ' && ') + "'", get_pty=True)
        # tmuxのセッションに入ってしまうため、exec_commandでもダメな可能性がある。
        # upterm の仕様で、ssh接続すると強制的に tmux の共有セッション(upterm)にアタッチされる。
        
        out = stdout.read().decode('utf-8')
        if out:
            print(out)
            
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
