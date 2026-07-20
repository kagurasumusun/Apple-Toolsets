#!/usr/bin/env python3
"""harvest_v11: 各 platform を独立接続で、5 個ずつ send して取得"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = '0z6pfERbIkK3HRrW097T'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/h11'
LOCAL = '/home/user/ibtool-py/fixtures/mass4'

SAMPLES = {
    'a': ('.xib', '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
<view contentMode="scaleToFill" id="v1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/><viewLayoutGuide key="safeArea" id="sa1"/><color key="backgroundColor" systemColor="bg"/></view>
</objects>
<resources><systemColor name="bg"><color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/></systemColor></resources>
</document>'''),
}


def process(name, ext, content):
    print(f'  {name}...')
    fn = f'{name}{ext}'
    localp = f'/tmp/{fn}'
    with open(localp, 'w') as f:
        f.write(content)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY)
    client.connect(HOST, port=PORT, username=USER, pkey=pkey,
                   allow_agent=False, look_for_keys=False, timeout=15)
    sftp = client.open_sftp()
    try:
        sftp.mkdir(REMOTE)
    except IOError:
        pass
    sftp.put(localp, f'{REMOTE}/{fn}')

    chan = client.get_transport().open_session(timeout=15)
    chan.get_pty(term='xterm', width=200, height=50)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)

    def send_and_wait(cmd, marker, timeout=20):
        chan.send(cmd + f' ; echo {marker}\n')
        buf = b''
        end = time.time() + timeout
        while time.time() < end:
            if chan.recv_ready():
                r = chan.recv(65536)
                if r:
                    buf += r
                    if marker.encode() in buf:
                        return
            else:
                time.sleep(0.02)
        return buf.decode('utf-8', errors='replace')[:200]

    out_ext = '.storyboardc' if ext == '.storyboard' else '.nib'

    # Step 1: setup + compile + first batch
    M = f'M_{name}_{time.time_ns() % 1000000:06d}'
    send_and_wait(f'cd {REMOTE} && rm -f {name}* && ibtool --compile {name}{out_ext} {fn} && ibtool --classes {fn} > {name}_classes.plist && ibtool --objects {fn} > {name}_objects.plist && ibtool --hierarchy {fn} > {name}_hierarchy.plist && ibtool --connections {fn} > {name}_connections.plist && ibtool --all {fn} > {name}_all.plist', M)
    # Step 2: more plist
    M = f'M2_{name}_{time.time_ns() % 1000000:06d}'
    send_and_wait(f'cd {REMOTE} && ibtool --version-history {fn} > {name}_version-history.plist && ibtool --localizable-strings {fn} > {name}_localizable-strings.plist && ibtool --localizable-all {fn} > {name}_localizable-all.plist && ibtool --localizable-geometry {fn} > {name}_localizable-geometry.plist && ibtool --localizable-stringarrays {fn} > {name}_localizable-stringarrays.plist', M)
    M = f'M3_{name}_{time.time_ns() % 1000000:06d}'
    send_and_wait(f'cd {REMOTE} && ibtool --localizable-other {fn} > {name}_localizable-other.plist && ibtool --localizable-to-many-relationships {fn} > {name}_localizable-to-many-relationships.plist && ibtool --warnings {fn} > {name}_warnings.plist && ibtool --errors {fn} > {name}_errors.plist && ibtool --notices {fn} > {name}_notices.plist', M)
    # Step 3: xliff + strings + write
    M = f'M4_{name}_{time.time_ns() % 1000000:06d}'
    send_and_wait(f'cd {REMOTE} && ibtool --export-xliff {name}.xlf --source-language en --target-language ja {fn} && ibtool --export-strings-file {name}.strings {fn} && ibtool --generate-strings-file {name}_gen.strings {fn}', M)
    M = f'M5_{name}_{time.time_ns() % 1000000:06d}'
    send_and_wait(f'cd {REMOTE} && ibtool --write {name}_out.xib {fn} && ibtool --upgrade --write {name}_up.xib {fn} && ibtool --remove-plugin-dependencies --write {name}_rpd.xib {fn} && ibtool --strip --compile {name}_strip{out_ext} {fn}', M)
    M = f'M6_{name}_{time.time_ns() % 1000000:06d}'
    send_and_wait(f'cd {REMOTE} && ibtool --all --output-format binary1 {fn} > {name}_all.bin && ibtool --all --output-format human-readable-text {fn} > {name}_all.txt', M)

    count = 0
    for fn2 in sftp.listdir(REMOTE):
        if fn2.startswith('.'):
            continue
        if not fn2.startswith(name):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn2}', f'{LOCAL}/{fn2}')
            count += 1
        except Exception:
            pass
    print(f'    {count} files')

    sftp.close()
    chan.close()
    client.close()


def main():
    os.makedirs(LOCAL, exist_ok=True)
    for name, (ext, content) in SAMPLES.items():
        process(name, ext, content)


if __name__ == '__main__':
    main()
