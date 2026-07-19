import paramiko
import time

def download_log():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(key_path)
    client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
    
    sftp = client.open_sftp()
    try:
        sftp.get("/private/tmp/run.log", "/home/user/run.log")
        print("Successfully downloaded /private/tmp/run.log!")
    except Exception as e:
        print("SFTP Download failed:", e)
        
    client.close()

if __name__ == "__main__":
    download_log()
