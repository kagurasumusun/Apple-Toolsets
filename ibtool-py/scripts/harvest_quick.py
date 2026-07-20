#!/usr/bin/env python3
"""harvest_quick: 高速版フィクスチャ取得 (time.sleep を最小化)"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_quick'
LOCAL = '/home/user/ibtool-py/fixtures/probe_quick'

XIB_IOS = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
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
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <view contentMode="scaleToFill" id="iN0-l3-epB">
            <rect key="frame" x="0.0" y="0.0" width="1920" height="1080"/>
        </view>
    </objects>
</document>'''

XIB_MAC = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.Cocoa.XIB" version="3.0" toolsVersion="22154" targetRuntime="macOS.Cocoa" propertyAccessControl="none" useAutolayout="YES">
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaPlugin" version="22131"/>
    </dependencies>
    <objects>
        <window title="Test" id="QvC-M9-y7g">
            <windowStyleMask key="styleMask" titled="YES" closable="YES"/>
            <rect key="contentRect" x="196" y="240" width="480" height="270"/>
            <view key="contentView" id="EiT-Mj-1SZ">
                <rect key="frame" x="0.0" y="0.0" width="480" height="270"/>
                <autoresizingMask key="autoresizingMask"/>
            </view>
        </window>
        <customObject id="-1" userLabel="File's Owner" customClass="NSApplication"/>
    </objects>
</document>'''

XIB_STORY = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" initialViewController="vXZ-lx-Hvc">
    <device id="retina6_12" orientation="portrait"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
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


def run(chan, cmd, t=0.3):
    chan.send(cmd + '\n')
    time.sleep(t)
    data = b''
    chan.settimeout(t + 0.5)
    try:
        while True:
            r = chan.recv(65536)
            if not r:
                break
            data += r
    except Exception:
        pass
    return data.decode('utf-8', errors='replace')


def main():
    os.makedirs(LOCAL, exist_ok=True)
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
    run(chan, f'rm -rf {REMOTE} && mkdir -p {REMOTE}', 0.5)

    templates = {
        'ios': XIB_IOS,
        'tvos': XIB_TVOS,
        'macos': XIB_MAC,
        'story': XIB_STORY,
    }
    for name, content in templates.items():
        with open(f'/tmp/{name}.xib', 'w') as f:
            f.write(content)
        if name == 'story':
            sftp.put(f'/tmp/{name}.xib', f'{REMOTE}/{name}.storyboard')
        else:
            sftp.put(f'/tmp/{name}.xib', f'{REMOTE}/{name}.xib')

    # Run all features (fast)
    for name in templates:
        ext = '.storyboard' if name == 'story' else '.xib'
        out_ext = '.storyboardc' if name == 'story' else '.nib'
        run(chan, f'cd {REMOTE} && ibtool --compile {name}{out_ext} {name}{ext} 2>&1', 0.5)
        for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                    'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                    'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                    'localizable-to-many-relationships']:
            run(chan, f'cd {REMOTE} && ibtool --{cmd} {name}{ext} > {name}_{cmd}.plist 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --export-xliff {name}.xlf --source-language en --target-language ja {name}{ext} 2>&1', 0.5)
        run(chan, f'cd {REMOTE} && ibtool --export-strings-file {name}.strings {name}{ext} 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --generate-strings-file {name}_gen.strings {name}{ext} 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --write {name}_out.xib {name}{ext} 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --upgrade --write {name}_up.xib {name}{ext} 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --remove-plugin-dependencies --write {name}_rpd.xib {name}{ext} 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --strip --compile {name}_strip{out_ext} {name}{ext} 2>&1', 0.5)
        run(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 {name}{ext} > {name}_all.bin 2>&1', 0.3)
        run(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text {name}{ext} > {name}_all.txt 2>&1', 0.3)

    for fn in sftp.listdir(REMOTE):
        if fn.startswith('.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn}', f'{LOCAL}/{fn}')
            print(f'  {fn}')
        except Exception as e:
            print(f'  err {fn}: {e}')

    sftp.close()
    chan.close()
    client.close()


if __name__ == '__main__':
    main()
