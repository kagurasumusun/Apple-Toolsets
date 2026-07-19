import paramiko
import time
import base64

def run_test():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(key_path)
    client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
    
    shell = client.invoke_shell(term='vt100', width=200, height=50)
    time.sleep(2)
    if shell.recv_ready(): shell.recv(65535)
    
    # Send Ctrl+C
    shell.send("\x03\n")
    time.sleep(1)
    
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

ACTOOL_DIR="/Users/runner/work/Apple-actool-py/Apple-actool-py"
cd $ACTOOL_DIR && git pull origin fix-bugs && cd -

rm -rf Assets.xcassets
mkdir -p Assets.xcassets/AppIcon.appiconset
echo '{"images": [{"idiom": "ios-marketing", "size": "1024x1024", "scale": "1x", "filename": "icon.png"}],"info": {"version": 1, "author": "xcode"}}' > Assets.xcassets/AppIcon.appiconset/Contents.json
dd if=/dev/urandom of=Assets.xcassets/AppIcon.appiconset/icon.png bs=1024 count=1024 2>/dev/null

export PYTHONPATH="$ACTOOL_DIR"
/opt/homebrew/bin/python3 -m actool_linux.nextgen Assets.xcassets --compile . --platform iphoneos --minimum-deployment-target 15.0 --app-icon AppIcon --optimize smart

# The user asked for iOS 16.2. The prompt says: "iOS26.2" probably meant 16.2 or 15.0. 
# We'll use Xcode default to target something. Let's see what sdk is available.
echo "--- XCODEBUILD INFO ---"
xcodebuild -showsdks

/usr/bin/xcrun -sdk iphonesimulator swiftc ContentView.swift aApp.swift -o TestApp -target x86_64-apple-ios16.0-simulator -emit-executable

rm -rf Payload TestApp.ipa
mkdir -p Payload/TestApp.app
cp TestApp Payload/TestApp.app/
cp Info.plist Payload/TestApp.app/
cp Assets.car Payload/TestApp.app/

/usr/bin/zip -r TestApp.ipa Payload
echo "BUILD_FINISHED_SUCCESSFULLY"
ls -la TestApp.ipa
pwd
"""
    b64 = base64.b64encode(cmd.encode('utf-8')).decode('utf-8')
    # Write directly to runner's home
    shell.send(f"echo '{b64}' | base64 -D > /Users/runner/run.sh && bash /Users/runner/run.sh > /Users/runner/run.log 2>&1 && echo 'TEST_DONE' || echo 'TEST_FAILED'\n")
    
    for _ in range(30):
        time.sleep(1)
        if shell.recv_ready():
            out = shell.recv(65535).decode('utf-8', errors='ignore')
            if "TEST_DONE" in out or "TEST_FAILED" in out:
                break
                
    # Now read the log via base64 encoded chunks to avoid terminal mess
    shell.send("\x03\nclear\necho '---B64LOG---' && base64 /Users/runner/run.log && echo '---ENDB64LOG---'\n")
    
    out_total = ""
    for _ in range(15):
        time.sleep(1)
        if shell.recv_ready():
            out_total += shell.recv(65535).decode('utf-8', errors='ignore')
            if "---ENDB64LOG---" in out_total:
                break
                
    client.close()
    
    import re
    # Extract base64 part
    start_idx = out_total.find('---B64LOG---')
    end_idx = out_total.find('---ENDB64LOG---', start_idx)
    if start_idx != -1 and end_idx != -1:
        b64_data = out_total[start_idx + len('---B64LOG---'):end_idx]
        b64_data = re.sub(r'[^A-Za-z0-9+/=]', '', b64_data)
        try:
            log_data = base64.b64decode(b64_data).decode('utf-8')
            with open("/home/user/run.log", "w") as f:
                f.write(log_data)
            print("Successfully extracted run.log to /home/user/run.log")
        except Exception as e:
            print("Failed to decode base64 log:", e)
    else:
        print("Could not find markers. Raw output:")
        print(out_total)

if __name__ == "__main__":
    run_test()
