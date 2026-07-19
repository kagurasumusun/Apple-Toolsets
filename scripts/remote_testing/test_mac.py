import paramiko
import time
import base64
import re
import sys

HOST = "uptermd.upterm.dev"
PORT = 22
USERNAME = "NZavJ93kKawd70bya6xE"
KEY_PATH = "/home/user/.ssh/id_ed25519"

def run_mac():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    client.connect(hostname=HOST, port=PORT, username=USERNAME, pkey=key, look_for_keys=False)
    shell = client.invoke_shell(term='vt100', width=200, height=50)
    time.sleep(2)
    if shell.recv_ready(): shell.recv(65535)

    script = """
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
export PYTHONPATH="$ACTOOL_DIR"

rm -rf Assets.xcassets
mkdir -p Assets.xcassets/AppIcon.appiconset
echo '{"images": [{"idiom": "ios-marketing", "size": "1024x1024", "scale": "1x", "filename": "icon.png"}],"info": {"version": 1, "author": "xcode"}}' > Assets.xcassets/AppIcon.appiconset/Contents.json
dd if=/dev/urandom of=Assets.xcassets/AppIcon.appiconset/icon.png bs=1024 count=1024 2>/dev/null

/opt/homebrew/bin/python3 -m actool_linux.nextgen Assets.xcassets --compile . --platform iphoneos --minimum-deployment-target 15.0 --app-icon AppIcon --optimize smart

echo '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>CFBundleExecutable</key><string>TestApp</string><key>CFBundleIdentifier</key><string>com.example.TestApp</string><key>CFBundleName</key><string>TestApp</string><key>CFBundleVersion</key><string>1</string><key>CFBundleShortVersionString</key><string>1.0</string><key>MinimumOSVersion</key><string>15.0</string></dict></plist>' > Info.plist

# WARNING fix for swift compilation on this mac
export SDKROOT="$(xcrun --sdk iphonesimulator --show-sdk-path)"
xcrun -sdk iphonesimulator swiftc ContentView.swift aApp.swift -o TestApp -target x86_64-apple-ios15.0-simulator -emit-executable

rm -rf Payload TestApp.ipa
mkdir -p Payload/TestApp.app
cp TestApp Payload/TestApp.app/
cp Info.plist Payload/TestApp.app/
cp Assets.car Payload/TestApp.app/
zip -r TestApp.ipa Payload > /dev/null

echo "--- TESTING CAR FILE WITH APPLE ASSETUTIL ---"
xcrun assetutil -I Payload/TestApp.app/Assets.car

python3 -c "import base64, sys; sys.stdout.write('@@@IPA_START@@@' + base64.b64encode(open('TestApp.ipa', 'rb').read()).decode('utf-8') + '@@@IPA_END@@@\\n')"
echo "DONE_ALL"
"""
    b64_script = base64.b64encode(script.encode('utf-8')).decode('utf-8')
    shell.send(f"echo '{b64_script}' | base64 -D > /tmp/run.sh && bash /tmp/run.sh\n")

    out_total = ""
    for i in range(120):
        time.sleep(1)
        if shell.recv_ready():
            chunk = shell.recv(65535).decode('utf-8', errors='ignore')
            out_total += chunk
            sys.stdout.write(chunk)
            sys.stdout.flush()
            if "DONE_ALL" in chunk or "@@@IPA_END@@@" in out_total:
                break
                
    start_idx = out_total.find('@@@IPA_START@@@')
    end_idx = out_total.find('@@@IPA_END@@@')
    if start_idx != -1 and end_idx != -1:
        data_str = out_total[start_idx+15:end_idx]
        data_str = re.sub(r'[^A-Za-z0-9+/=]', '', data_str)
        data_str += "=" * ((4 - len(data_str) % 4) % 4)
        with open("/home/user/TestApp.ipa", "wb") as f:
            f.write(base64.b64decode(data_str))
        print("\\nSuccessfully downloaded TestApp.ipa to /home/user/TestApp.ipa")
    else:
        print("\\nFailed. Output too large or missing markers.")

if __name__ == "__main__":
    run_mac()
