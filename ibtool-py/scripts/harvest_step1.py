#!/usr/bin/env python3
"""
harvest_step1.py - フィクスチャ取得 Step1: 1 つの xib で全機能実行して取得
"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_probe'
LOCAL = '/home/user/ibtool-py/fixtures/probe'

XIB = '''<?xml version="1.0" encoding="UTF-8"?>
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

    # Setup
    run(chan, f'rm -rf {REMOTE} && mkdir -p {REMOTE}', 1)
    with open('/tmp/ios_view.xib', 'w') as f:
        f.write(XIB)
    sftp.put('/tmp/ios_view.xib', f'{REMOTE}/ios_view.xib')
    print('uploaded')

    # Run ibtool commands (limited set)
    run(chan, f'cd {REMOTE} && ibtool --compile ios_view.nib ios_view.xib 2>&1', 3)
    run(chan, f'cd {REMOTE} && ibtool --classes ios_view.xib > ios_view_classes.plist 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --objects ios_view.xib > ios_view_objects.plist 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --hierarchy ios_view.xib > ios_view_hierarchy.plist 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --connections ios_view.xib > ios_view_connections.plist 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --all ios_view.xib > ios_view_all.plist 2>&1', 3)
    run(chan, f'cd {REMOTE} && ibtool --version-history ios_view.xib > ios_view_vh.plist 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --export-strings-file ios_view.strings ios_view.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --generate-strings-file ios_view_gen.strings ios_view.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --export-xliff ios_view.xlf --source-language en --target-language ja ios_view.xib 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --generate-xliff ios_view_gen.xlf --source-language en --target-language ja ios_view.xib 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --warnings ios_view.xib > ios_view_warn.plist 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --errors ios_view.xib > ios_view_err.plist 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --notices ios_view.xib > ios_view_notice.plist 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --localizable-all ios_view.xib > ios_view_locall.plist 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text ios_view.xib > ios_view_all.txt 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 ios_view.xib > ios_view_all.bin 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --write ios_view_out.xib ios_view.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --strip --compile ios_view_strip.nib ios_view.xib 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --upgrade --write ios_view_up.xib ios_view.xib 2>&1', 1)

    # Get all
    for fn in sftp.listdir(REMOTE):
        if fn.startswith('.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn}', f'{LOCAL}/{fn}')
            print(f'got {fn}')
        except Exception as e:
            print(f'err {fn}: {e}')

    sftp.close()
    chan.close()
    client.close()


if __name__ == '__main__':
    main()
