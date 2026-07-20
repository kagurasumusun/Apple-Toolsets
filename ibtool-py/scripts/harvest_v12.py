#!/usr/bin/env python3
"""harvest_v12: ステップ毎 = 1 接続 (毎回 bash 起動で send-keys ブロック回避)

各ステップ 1 SSH 接続。各 platform 6 接続。
"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = '0z6pfERbIkK3HRrW097T'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/h12'
LOCAL = '/home/user/ibtool-py/fixtures/mass5'

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


def make_chan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY)
    client.connect(HOST, port=PORT, username=USER, pkey=pkey,
                   allow_agent=False, look_for_keys=False, timeout=15)
    sftp = client.open_sftp()
    chan = client.get_transport().open_session(timeout=15)
    chan.get_pty(term='xterm', width=200, height=50)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)
    return client, sftp, chan


def send_and_wait(chan, cmd, marker, timeout=15):
    chan.send(cmd + f' ; echo {marker}\n')
    buf = b''
    end = time.time() + timeout
    while time.time() < end:
        if chan.recv_ready():
            r = chan.recv(65536)
            if r:
                buf += r
                if marker.encode() in buf:
                    return True
        else:
            time.sleep(0.02)
    return False


def process(name, ext, content):
    print(f'  {name}...')
    fn = f'{name}{ext}'
    localp = f'/tmp/{fn}'
    with open(localp, 'w') as f:
        f.write(content)

    out_ext = '.storyboardc' if ext == '.storyboard' else '.nib'
    n = name

    steps = [
        # step, cmd
        ('compile', f'cd {REMOTE} && rm -f {n}* && ibtool --compile {n}{out_ext} {fn}'),
        ('dumps1', f'cd {REMOTE} && ibtool --classes {fn} > {n}_classes.plist && ibtool --objects {fn} > {n}_objects.plist && ibtool --hierarchy {fn} > {n}_hierarchy.plist && ibtool --connections {fn} > {n}_connections.plist && ibtool --all {fn} > {n}_all.plist'),
        ('dumps2', f'cd {REMOTE} && ibtool --version-history {fn} > {n}_version-history.plist && ibtool --localizable-strings {fn} > {n}_localizable-strings.plist && ibtool --localizable-all {fn} > {n}_localizable-all.plist && ibtool --localizable-geometry {fn} > {n}_localizable-geometry.plist && ibtool --localizable-stringarrays {fn} > {n}_localizable-stringarrays.plist'),
        ('dumps3', f'cd {REMOTE} && ibtool --localizable-other {fn} > {n}_localizable-other.plist && ibtool --localizable-to-many-relationships {fn} > {n}_localizable-to-many-relationships.plist && ibtool --warnings {fn} > {n}_warnings.plist && ibtool --errors {fn} > {n}_errors.plist && ibtool --notices {fn} > {n}_notices.plist'),
        ('xliff', f'cd {REMOTE} && ibtool --export-xliff {n}.xlf --source-language en --target-language ja {fn} && ibtool --export-strings-file {n}.strings {fn} && ibtool --generate-strings-file {n}_gen.strings {fn}'),
        ('write', f'cd {REMOTE} && ibtool --write {n}_out.xib {fn} && ibtool --upgrade --write {n}_up.xib {fn} && ibtool --remove-plugin-dependencies --write {n}_rpd.xib {fn} && ibtool --strip --compile {n}_strip{out_ext} {fn}'),
        ('formats', f'cd {REMOTE} && ibtool --all --output-format binary1 {fn} > {n}_all.bin && ibtool --all --output-format human-readable-text {fn} > {n}_all.txt'),
    ]

    # Initial: upload via sftp using first connection
    client, sftp, chan = make_chan()
    try:
        sftp.mkdir(REMOTE)
    except IOError:
        pass
    sftp.put(localp, f'{REMOTE}/{fn}')
    sftp.close()
    chan.close()
    client.close()

    # Run each step in its own connection
    for step_name, cmd in steps:
        client, sftp, chan = make_chan()
        M = f'M_{step_name}_{time.time_ns() % 1000000:06d}'
        ok = send_and_wait(chan, cmd, M, timeout=20)
        if not ok:
            print(f'    {step_name}: timeout/partial')
        chan.close()
        client.close()

    # Final: get all via sftp using a fresh connection
    client, sftp, chan = make_chan()
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
    sftp.close()
    chan.close()
    client.close()
    print(f'    {count} files')


def main():
    os.makedirs(LOCAL, exist_ok=True)
    for name, (ext, content) in SAMPLES.items():
        process(name, ext, content)


if __name__ == '__main__':
    main()
