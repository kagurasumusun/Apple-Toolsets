import paramiko
import sys
import time

def run_upterm_test():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    
    # 接続のセットアップ
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {username}@{host}...")
        # 鍵認証などは指定せず、デフォルトで接続
        client.connect(hostname=host, port=port, username=username, password="", look_for_keys=False)
        print("Connected!")
        
        # ptyを強制的に使ってインタラクティブシェルを開く
        shell = client.invoke_shell(term='xterm', width=132, height=43)
        time.sleep(2)
        
        # 画面の出力を受け取る
        if shell.recv_ready():
            output = shell.recv(4096).decode('utf-8', errors='replace')
            print("--- Output from Upterm ---")
            print(output)
            print("--------------------------")
            
        print("Closing connection...")
        shell.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
