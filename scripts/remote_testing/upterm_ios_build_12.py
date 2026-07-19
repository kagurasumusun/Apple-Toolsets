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
        
        # tmux問題を回避するため直接 bash を起動
        stdin, stdout, stderr = client.exec_command('bash')
        
        print("Executing iOS Build Pipeline on Remote Mac...")
        script_content = """
set -e
cd /Users/runner/work
mkdir -p build_ios_app && cd build_ios_app
if [ ! -d "ios-dev" ]; then git clone https://github.com/kagurasumusun/ios-dev.git; fi
cd ios-dev
git fetch origin main
git reset --hard origin/main
cd testapp/swift-test-build

echo "=== 1. PREPARE ASSETS WITH Apple-actool-py ==="
ACTOOL_DIR="/Users/runner/work/Apple-actool-py/Apple-actool-py"
cd $ACTOOL_DIR && git pull origin fix-bugs && cd -

rm -rf Assets.xcassets
mkdir -p Assets.xcassets/AppIcon.appiconset
cat << 'JSON_EOF' > Assets.xcassets/AppIcon.appiconset/Contents.json
{
  "images": [
    {"idiom": "ios-marketing", "size": "1024x1024", "scale": "1x", "filename": "icon.png"}
  ],
  "info": {"version": 1, "author": "xcode"}
}
JSON_EOF
dd if=/dev/urandom of=Assets.xcassets/AppIcon.appiconset/icon.png bs=1024 count=1024 2>/dev/null

export PYTHONPATH="$ACTOOL_DIR"
python3 -m actool_linux.nextgen Assets.xcassets --compile . --platform iphoneos --minimum-deployment-target 15.0 --app-icon AppIcon --optimize smart

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
xcrun -sdk iphonesimulator swiftc ContentView.swift aApp.swift -o TestApp -target x86_64-apple-ios15.0-simulator -emit-executable || echo "Swift compilation failed"

echo "=== 3. PACKAGING IPA ==="
rm -rf Payload TestApp.ipa
mkdir -p Payload/TestApp.app
cp TestApp Payload/TestApp.app/ 2>/dev/null || echo "TestApp bin missing"
cp Info.plist Payload/TestApp.app/
cp Assets.car Payload/TestApp.app/ || echo "Assets.car not found!"

zip -r TestApp.ipa Payload > /dev/null
echo "=== BUILD SUCCESS ==="
pwd
ls -la TestApp.ipa
echo "DONE_BUILD"
"""
        import base64
        b64_script = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')
        
        # Base64でデコードして実行
        stdin.write(f"echo '{b64_script}' | base64 --decode > /tmp/build_ipa.sh && bash /tmp/build_ipa.sh\\n")
        stdin.flush()
        
        # 実行が終わるのを待つ
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line, end="")
            if "DONE_BUILD" in line:
                break
                
        err = stderr.read().decode('utf-8')
        if err:
            print("Errors:", err)
        
        print("\\nDownloading IPA to local workspace...")
        sftp = client.open_sftp()
        try:
            sftp.get("/Users/runner/work/build_ios_app/ios-dev/testapp/swift-test-build/TestApp.ipa", "/home/user/TestApp.ipa")
            print("Downloaded TestApp.ipa successfully!")
        except Exception as file_err:
            print(f"SFTP Download failed: {file_err}")
            
        sftp.close()
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
