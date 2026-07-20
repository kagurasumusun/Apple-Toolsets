#!/usr/bin/env python3
"""harvest_v8: 1 接続で複数 platform 処理 (短いコマンド単位で send-keys)"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_v8'
LOCAL = '/home/user/ibtool-py/fixtures/probe_v8'


def make_chan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY)
    client.connect(HOST, port=PORT, username=USER, pkey=pkey,
                   allow_agent=False, look_for_keys=False, timeout=15)
    sftp = client.open_sftp()
    chan = client.get_transport().open_session(timeout=15)
    chan.get_pty(term='xterm', width=132, height=43)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)
    return client, sftp, chan


def run_one(chan, cmd, timeout=8):
    """Run a short command, return output stripped of ANSI."""
    M = f'IBEND{time.time_ns() % 1000000:06d}'
    chan.send(cmd + f' ; echo {M}\n')
    buf = b''
    end = time.time() + timeout
    while time.time() < end:
        if chan.recv_ready():
            try:
                r = chan.recv(65536)
                if r:
                    buf += r
                    if M.encode() in buf:
                        idx = buf.find(M.encode())
                        out = buf[:idx].decode('utf-8', errors='replace')
                        # strip ANSI
                        out = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', out)
                        out = re.sub(r'\x1b[\(\)][0-9A-Za-z]', '', out)
                        out = re.sub(r'\x1b[\[\]()][0-9;?]*[A-Za-z]?', '', out)
                        out = re.sub(r'\r', '', out)
                        return out
            except Exception:
                pass
        else:
            time.sleep(0.05)
    return buf.decode('utf-8', errors='replace')


def process(name, ext, content, sftp, chan):
    print(f'  {name}{ext}...')
    with open(f'/tmp/{name}{ext}', 'w') as f:
        f.write(content)
    sftp.put(f'/tmp/{name}{ext}', f'{REMOTE}/{name}{ext}')

    out_ext = '.storyboardc' if ext == '.storyboard' else '.nib'

    # Delete ONLY previous outputs (not source!)
    run_one(chan, f'cd {REMOTE} && rm -f {name}.nib {name}.storyboardc {name}*.plist {name}.xlf {name}.strings {name}_gen.strings {name}_*.xib {name}_*.bin {name}_*.txt {name}_strip.nib {name}_strip.storyboardc', 2)
    # compile
    run_one(chan, f'cd {REMOTE} && ibtool --compile {name}{out_ext} {name}{ext}', 8)
    # plist dumps
    for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                'localizable-to-many-relationships']:
        run_one(chan, f'cd {REMOTE} && ibtool --{cmd} {name}{ext} > {name}_{cmd}.plist', 6)
    # xliff, strings
    run_one(chan, f'cd {REMOTE} && ibtool --export-xliff {name}.xlf --source-language en --target-language ja {name}{ext}', 8)
    run_one(chan, f'cd {REMOTE} && ibtool --export-strings-file {name}.strings {name}{ext}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --generate-strings-file {name}_gen.strings {name}{ext}', 4)
    # write
    run_one(chan, f'cd {REMOTE} && ibtool --write {name}_out.xib {name}{ext}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --upgrade --write {name}_up.xib {name}{ext}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --remove-plugin-dependencies --write {name}_rpd.xib {name}{ext}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --strip --compile {name}_strip{out_ext} {name}{ext}', 6)
    run_one(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 {name}{ext} > {name}_all.bin', 6)
    run_one(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text {name}{ext} > {name}_all.txt', 6)

    # sftp get
    for fn in sftp.listdir(REMOTE):
        if fn.startswith('.') or not fn.startswith(name):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn}', f'{LOCAL}/{fn}')
        except Exception as e:
            print(f'    err {fn}: {e}')


def main():
    os.makedirs(LOCAL, exist_ok=True)
    client, sftp, chan = make_chan()
    try:
        sftp.mkdir(REMOTE)
    except IOError:
        pass

    XIB_IOS = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait" appearance="light"/>
<dependencies>
<plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
<capability name="Safe area layout guides" minToolsVersion="9.0"/>
</dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
<view contentMode="scaleToFill" id="iN0-l3-epB">
<rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
<autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
<viewLayoutGuide key="safeArea" id="Bcu-3y-fUS"/>
<color key="backgroundColor" systemColor="systemBackgroundColor"/>
</view>
</objects>
<resources>
<systemColor name="systemBackgroundColor">
<color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
</systemColor>
</resources>
</document>'''

    XIB_TVOS = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" variant="tvOS" propertyAccessControl="none" useAutolayout="YES">
<device id="apple_tv" orientation="landscape"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="iN0-l3-epB"><rect key="frame" x="0.0" y="0.0" width="1920" height="1080"/></view>
</objects>
</document>'''

    XIB_MAC = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.Cocoa.XIB" version="3.0" toolsVersion="22154" targetRuntime="macOS.Cocoa" propertyAccessControl="none" useAutolayout="YES">
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaPlugin" version="22131"/></dependencies>
<objects>
<window title="Test" id="QvC-M9-y7g"><windowStyleMask key="styleMask" titled="YES"/><rect key="contentRect" x="196" y="240" width="480" height="270"/>
<view key="contentView" id="EiT-Mj-1SZ"><rect key="frame" x="0.0" y="0.0" width="480" height="270"/><autoresizingMask key="autoresizingMask"/></view>
</window>
<customObject id="-1" userLabel="File's Owner" customClass="NSApplication"/>
</objects>
</document>'''

    XIB_XR = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" variant="xrOS" propertyAccessControl="none" useAutolayout="YES">
<device id="xr" orientation="landscape"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="iN0-l3-epB"><rect key="frame" x="0.0" y="0.0" width="1280" height="720"/></view>
</objects>
</document>'''

    XIB_WATCH = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.WatchKit.XIB" version="3.0" toolsVersion="22154" targetRuntime="watchKit" propertyAccessControl="none" useAutolayout="YES">
<device id="watch42"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.WatchKitPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<label alignment="center" id="Lbl-1"><rect key="frame" x="0" y="0" width="100" height="30"/></label>
</objects>
</document>'''

    XIB_STORY = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" initialViewController="vXZ-lx-Hvc">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<scenes>
<scene sceneID="tne-QT-ifu">
<objects>
<viewController id="vXZ-lx-Hvc" customClass="ViewController" sceneMemberID="viewController">
<view key="view" contentMode="scaleToFill" id="kh9-bI-dsS">
<rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
<autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
</view>
</viewController>
<placeholder placeholderIdentifier="IBFirstResponder" id="x5A-6p-PRh" sceneMemberID="firstResponder"/>
</objects>
<point key="canvasLocation" x="53" y="375"/>
</scene>
</scenes>
</document>'''

    templates = [
        ('ios', '.xib', XIB_IOS),
        ('tvos', '.xib', XIB_TVOS),
        ('macos', '.xib', XIB_MAC),
        ('xr', '.xib', XIB_XR),
        ('watch', '.xib', XIB_WATCH),
        ('story', '.storyboard', XIB_STORY),
    ]
    for name, ext, content in templates:
        process(name, ext, content, sftp, chan)

    sftp.close()
    chan.close()
    client.close()


if __name__ == '__main__':
    main()
