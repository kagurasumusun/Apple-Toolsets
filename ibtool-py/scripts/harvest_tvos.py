#!/usr/bin/env python3
"""harvest_tvos: tvOS xib の全機能フィクスチャ取得 (1 ファイル 1 ステップ)"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_tvos'
LOCAL = '/home/user/ibtool-py/fixtures/probe_tvos'


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

    XIB = '''<?xml version="1.0" encoding="UTF-8"?>
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
</document>'''

    with open('/tmp/tvos.xib', 'w') as f:
        f.write(XIB)
    sftp.put('/tmp/tvos.xib', f'{REMOTE}/tvos.xib')

    base = 'tvos'
    run(chan, f'cd {REMOTE} && ibtool --compile {base}.nib tvos.xib 2>&1', 3)
    for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                'localizable-to-many-relationships']:
        run(chan, f'cd {REMOTE} && ibtool --{cmd} tvos.xib > {base}_{cmd}.plist 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --export-xliff {base}.xlf --source-language en --target-language ja tvos.xib 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --export-strings-file {base}.strings tvos.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --generate-strings-file {base}_gen.strings tvos.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --write {base}_out.xib tvos.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --upgrade --write {base}_up.xib tvos.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --remove-plugin-dependencies --write {base}_rpd.xib tvos.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --strip --compile {base}_strip.nib tvos.xib 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --target-device appletv --write {base}_td.xib tvos.xib 2>&1', 1)
    run(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 tvos.xib > {base}_all.bin 2>&1', 2)
    run(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text tvos.xib > {base}_all.txt 2>&1', 2)

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
