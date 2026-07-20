#!/usr/bin/env python3
"""harvest_step2: 複数 platform + 複数機能 + storyboard フィクスチャ取得"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_probe2'
LOCAL = '/home/user/ibtool-py/fixtures/probe2'


def run(chan, cmd, t=2):
    chan.send(cmd + '\n')
    time.sleep(t)
    data = b''
    chan.settimeout(t)
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
    run(chan, f'rm -rf {REMOTE} && mkdir -p {REMOTE}', 1)

    # Templates: tvOS, macOS, watchOS, storyboard
    templates = {
        'tvos.xib': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" variant="tvOS" propertyAccessControl="none" useAutolayout="YES" colorMatched="YES">
    <device id="apple_tv" orientation="landscape" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <view contentMode="scaleToFill" id="iN0-l3-epB">
            <rect key="frame" x="0.0" y="0.0" width="1920" height="1080"/>
            <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
        </view>
    </objects>
</document>''',
        'macos.xib': '''<?xml version="1.0" encoding="UTF-8"?>
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
</document>''',
        'watchos.xib': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.WatchKit.XIB" version="3.0" toolsVersion="22154" targetRuntime="watchKit" propertyAccessControl="none" useAutolayout="YES">
    <device id="watch42"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.WatchKitPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <label alignment="center" id="Lbl-1">
            <rect key="frame" x="0" y="0" width="100" height="30"/>
        </label>
    </objects>
</document>''',
        'storyboard.storyboard': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="vXZ-lx-Hvc">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <scenes>
        <scene sceneID="tne-QT-ifu">
            <objects>
                <viewController id="vXZ-lx-Hvc" customClass="ViewController" sceneMemberID="viewController">
                    <layoutGuides>
                        <viewControllerLayoutGuide type="top" id="Llm-lL-Icb"/>
                    </layoutGuides>
                    <view key="view" contentMode="scaleToFill" id="kh9-bI-dsS">
                        <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <viewLayoutGuide key="safeArea" id="Bcu-3y-fUS"/>
                        <color key="backgroundColor" systemColor="systemBackgroundColor"/>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="x5A-6p-PRh" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="53" y="375"/>
        </scene>
    </scenes>
    <resources>
        <systemColor name="systemBackgroundColor">
            <color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
        </systemColor>
    </resources>
</document>''',
    }

    for name, content in templates.items():
        with open(f'/tmp/{name}', 'w') as f:
            f.write(content)
        sftp.put(f'/tmp/{name}', f'{REMOTE}/{name}')

    # For each, run all features
    for name in templates:
        base = name.replace('.xib', '').replace('.storyboard', '')
        # Special compile target for storyboard
        if 'storyboard' in name:
            run(chan, f'cd {REMOTE} && ibtool --compile {base}.storyboardc {name} 2>&1', 3)
        else:
            run(chan, f'cd {REMOTE} && ibtool --compile {base}.nib {name} 2>&1', 3)
        # Standard dump
        for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                    'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                    'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                    'localizable-to-many-relationships']:
            run(chan, f'cd {REMOTE} && ibtool --{cmd} {name} > {base}_{cmd}.plist 2>&1', 2)
        # xliff
        run(chan, f'cd {REMOTE} && ibtool --export-xliff {base}.xlf --source-language en --target-language ja {name} 2>&1', 2)
        # strings
        run(chan, f'cd {REMOTE} && ibtool --export-strings-file {base}.strings {name} 2>&1', 1)
        run(chan, f'cd {REMOTE} && ibtool --generate-strings-file {base}_gen.strings {name} 2>&1', 1)
        # write
        run(chan, f'cd {REMOTE} && ibtool --write {base}_out.xib {name} 2>&1', 1)
        # upgrade + write
        run(chan, f'cd {REMOTE} && ibtool --upgrade --write {base}_up.xib {name} 2>&1', 1)
        # remove-plugin-deps
        run(chan, f'cd {REMOTE} && ibtool --remove-plugin-dependencies --write {base}_rpd.xib {name} 2>&1', 1)
        # strip
        run(chan, f'cd {REMOTE} && ibtool --strip --compile {base}_strip.nib {name} 2>&1', 2)
        # target-device
        run(chan, f'cd {REMOTE} && ibtool --target-device iphone --write {base}_td.xib {name} 2>&1', 1)
        # binary1
        run(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 {name} > {base}_all.bin 2>&1', 2)
        # human
        run(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text {name} > {base}_all.txt 2>&1', 2)

    for fn in sftp.listdir(REMOTE):
        if fn.startswith('.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn}', f'{LOCAL}/{fn}')
        except Exception as e:
            print(f'err {fn}: {e}')

    sftp.close()
    chan.close()
    client.close()


if __name__ == '__main__':
    main()
