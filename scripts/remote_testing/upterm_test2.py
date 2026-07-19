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
        print(f"Connecting to {username}@{host} with key {key_path}...")
        key = paramiko.Ed25519Key.from_private_key_file(key_path)
        client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
        print("Connected!")
        
        # ptyを強制的に使ってインタラクティブシェルを開く
        shell = client.invoke_shell(term='xterm', width=132, height=43)
        time.sleep(2)
        
        # 初期出力を受け取る
        if shell.recv_ready():
            output = shell.recv(65535).decode('utf-8', errors='replace')
            print("--- Initial Output ---")
            print(output)
            
        print("Sending tests...")
        # 環境の確認
        shell.send("ls -la\\n")
        time.sleep(1)
        
        if shell.recv_ready():
            print("--- Command Output ---")
            print(shell.recv(65535).decode('utf-8', errors='replace'))
            
        print("Closing connection...")
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
