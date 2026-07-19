import paramiko
import time
import base64
import re

HOST = "uptermd.upterm.dev"
PORT = 22
USERNAME = "NZavJ93kKawd70bya6xE"
KEY_PATH = "/home/user/.ssh/id_ed25519"

def get_shell():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    client.connect(hostname=HOST, port=PORT, username=USERNAME, pkey=key, look_for_keys=False)
    shell = client.invoke_shell(term='vt100', width=200, height=50)
    time.sleep(2)
    if shell.recv_ready(): shell.recv(65535)
    return client, shell

def run_command(shell, cmd, timeout=120):
    b64_cmd = base64.b64encode(cmd.encode('utf-8')).decode('utf-8')
    shell.send("rm -f /tmp/cmd.done /tmp/cmd.log\n")
    time.sleep(0.5)
    wrapper = f"echo '{b64_cmd}' | base64 -D > /tmp/cmd.sh && bash /tmp/cmd.sh > /tmp/cmd.log 2>&1 ; echo DONE > /tmp/cmd.done\n"
    shell.send(wrapper)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        shell.send("cat /tmp/cmd.done 2>/dev/null\n")
        time.sleep(2)
        if shell.recv_ready():
            out = shell.recv(65535).decode('utf-8', errors='ignore')
            if 'DONE' in out:
                break
                
    remote_py = '''import base64
try:
    with open('/tmp/cmd.log', 'rb') as f: data = f.read()
    print("@@@LOG_START@@@" + base64.b64encode(data).decode('utf-8') + "@@@LOG_END@@@")
except Exception as e:
    print("@@@LOG_START@@@ERROR:" + str(e) + "@@@LOG_END@@@")
'''
    shell.send(f"python3 -c \"{remote_py}\"\n")
    
    out_total = ""
    start_time = time.time()
    while time.time() - start_time < 30:
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if "@@@LOG_END@@@" in out_total:
                break
                
    start_idx = out_total.find('@@@LOG_START@@@')
    end_idx = out_total.find('@@@LOG_END@@@')
    if start_idx != -1 and end_idx != -1:
        data_str = out_total[start_idx+15:end_idx]
        if data_str.startswith("ERROR:"):
            return data_str
        data_str = re.sub(r'[^A-Za-z0-9+/=]', '', data_str)
        data_str += "=" * ((4 - len(data_str) % 4) % 4)
        return base64.b64decode(data_str).decode('utf-8', errors='replace')
    return "Failed to extract log: " + out_total

if __name__ == "__main__":
    client, shell = get_shell()
    
    cmd = """
set -e
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
cd /Users/runner/work
mkdir -p build_ios_app && cd build_ios_app
if [ ! -d "ios-dev" ]; then git clone https://github.com/kagurasumusun/ios-dev.git; fi
cd ios-dev
git fetch origin main
git reset --hard origin/main
cd testapp/swift-test-build

rm -rf Assets.xcassets
mkdir -p Assets.xcassets/AppIcon.appiconset
echo '{"images": [{"idiom": "ios-marketing", "size": "1024x1024", "scale": "1x", "filename": "icon.png"}],"info": {"version": 1, "author": "xcode"}}' > Assets.xcassets/AppIcon.appiconset/Contents.json
dd if=/dev/urandom of=Assets.xcassets/AppIcon.appiconset/icon.png bs=1024 count=1024 2>/dev/null

echo '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>CFBundleExecutable</key><string>TestApp</string><key>CFBundleIdentifier</key><string>com.example.TestApp</string><key>CFBundleName</key><string>TestApp</string><key>CFBundleVersion</key><string>1</string><key>CFBundleShortVersionString</key><string>1.0</string><key>MinimumOSVersion</key><string>16.2</string></dict></plist>' > Info.plist

# Check xcode
xcodebuild -showsdks

# Let's try 16.2 or 16.4 or latest available
xcrun -sdk iphonesimulator swiftc ContentView.swift aApp.swift -o TestApp -emit-executable

rm -rf Payload TestApp.ipa
mkdir -p Payload/TestApp.app
cp TestApp Payload/TestApp.app/
cp Info.plist Payload/TestApp.app/
# (we skipped car for now just to see if swiftc works)
zip -r TestApp.ipa Payload
pwd
ls -la TestApp.ipa
"""
    log = run_command(shell, cmd, timeout=60)
    print("LOG:")
    print(log)
    client.close()
