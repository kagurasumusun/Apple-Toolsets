import paramiko
import sys
import time
import re

def clean_tmux_output(output):
    # ANSI escape sequences と tmux の制御文字を頑張って削除する
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean = ansi_escape.sub('', output)
    # [K や不要な文字列を削除
    clean = clean.replace('[K', '').replace('\x0f', '').replace('\x07', '')
    # 空行の連続を削除
    clean = re.sub(r'\n\s*\n', '\n', clean)
    return clean

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
        shell = client.invoke_shell(term='vt100', width=200, height=50)
        time.sleep(2)
        
        if shell.recv_ready():
            shell.recv(65535) # Clear initial buffer
            
        # 1行のワンライナーで実行し、ファイルに書き出させてからcatで読む作戦
        cmd = "cd /Users/runner/work/Apple-actool-py/Apple-actool-py && git fetch origin fix-bugs && git checkout fix-bugs && git pull origin fix-bugs && export PYTHONPATH=. && rm -rf out_test_mac && python3 -m actool_linux tests/test_data/test.xcassets --compile out_test_mac --platform iphoneos --minimum-deployment-target 15.0 && xcrun assetutil -I out_test_mac/Assets.car > result.json && echo 'DONE_COMPILING'"
        
        shell.send(cmd + "\n")
        time.sleep(5)
        
        if shell.recv_ready():
            shell.recv(65535)
            
        # 結果を読む
        shell.send("head -n 25 result.json\n")
        time.sleep(2)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        print("=== Results from Remote Mac ===")
        print(clean_tmux_output(output))
        
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
