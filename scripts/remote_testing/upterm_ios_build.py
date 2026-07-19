import paramiko
import time
import re

def clean_tmux_output(output):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean = ansi_escape.sub('', output)
    clean = clean.replace('[K', '').replace('\x0f', '').replace('\x07', '')
    clean = re.sub(r'\n\s*\n', '\n', clean)
    return clean

def run_upterm_test():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        key = paramiko.Ed25519Key.from_private_key_file(key_path)
        client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
        
        shell = client.invoke_shell(term='vt100', width=200, height=50)
        time.sleep(2)
        if shell.recv_ready(): shell.recv(65535)
            
        print("Executing iOS Build Pipeline on Remote Mac...")
        cmd = """
cd /Users/runner/work
mkdir -p build_ios_app && cd build_ios_app
git clone https://github.com/kagurasumusun/ios-dev.git || true
cd ios-dev
git pull

# Go to testapp dir
cd testapp/swift-test-build

# Replace the compilation to use our Apple-actool-py compiler
echo "=== 1. PREPARE ASSETS WITH Apple-actool-py ==="
# Setup actool-py repo path
ACTOOL_DIR="/Users/runner/work/Apple-actool-py/Apple-actool-py"
# Prepare an Assets.xcassets dir
mkdir -p Assets.xcassets/AppIcon.appiconset
cat << 'JSON_EOF' > Assets.xcassets/AppIcon.appiconset/Contents.json
{
  "images": [
    {"idiom": "ios-marketing", "size": "1024x1024", "scale": "1x", "filename": "icon.png"}
  ],
  "info": {"version": 1, "author": "xcode"}
}
JSON_EOF
# Dummy image for icon
dd if=/dev/urandom of=Assets.xcassets/AppIcon.appiconset/icon.png bs=1024 count=1024

# NextGen 究極モード(Smart) でコンパイル
export PYTHONPATH="$ACTOOL_DIR"
python3 -m actool_linux.nextgen Assets.xcassets --compile . --platform iphoneos --minimum-deployment-target 15.0 --app-icon AppIcon --optimize smart

# Create Info.plist
cat << 'PLIST_EOF' > Info.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>TestApp</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.TestApp</string>
    <key>CFBundleName</key>
    <string>TestApp</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>MinimumOSVersion</key>
    <string>15.0</string>
</dict>
</plist>
PLIST_EOF

echo "=== 2. COMPILING SWIFT ==="
# Compile swift file for iOS simulator (easier without code signing)
xcrun -sdk iphonesimulator swiftc ContentView.swift aApp.swift -o TestApp -target x86_64-apple-ios15.0-simulator -emit-executable

echo "=== 3. PACKAGING IPA ==="
mkdir -p Payload/TestApp.app
cp TestApp Payload/TestApp.app/
cp Info.plist Payload/TestApp.app/
cp Assets.car Payload/TestApp.app/ || echo "Assets.car not found!"

zip -r TestApp.ipa Payload
echo "=== BUILD SUCCESS ==="
ls -la TestApp.ipa
"""
        shell.send(cmd.replace('\n', '\r'))
        
        for _ in range(40):
            time.sleep(1)
            if shell.recv_ready():
                out = shell.recv(65535).decode('utf-8', errors='ignore')
                if "=== BUILD SUCCESS ===" in clean_tmux_output(out):
                    break
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        print("=== Results from Remote Mac ===")
        print(clean_tmux_output(output))
                
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
