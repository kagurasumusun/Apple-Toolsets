#!/usr/bin/env python3
"""harvest_v14: 大量フィクスチャ取得 (複数 send 安定版)"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = '0z6pfERbIkK3HRrW097T'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/h14'
LOCAL = '/home/user/ibtool-py/fixtures/mass7'

XIB_IOS = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
<view contentMode="scaleToFill" id="v1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/><viewLayoutGuide key="safeArea" id="sa1"/><color key="backgroundColor" systemColor="bg"/></view>
</objects>
<resources><systemColor name="bg"><color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/></systemColor></resources>
</document>'''


def process(name, content):
    print(f'  {name}...')
    fn = f'{name}.xib'
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

    # Disable completion
    M = f'B_{time.time_ns() % 1000000:06d}'
    chan.send(f"bind 'set disable-completion on' 2>/dev/null ; echo {M}\n")
    buf = b''
    end = time.time() + 5
    while time.time() < end:
        if chan.recv_ready():
            r = chan.recv(65536)
            if r:
                buf += r
                if M.encode() in buf:
                    break
        else:
            time.sleep(0.05)

    def send_wait(cmd, timeout=20):
        M = f'M_{time.time_ns() % 1000000:06d}'
        chan.send(cmd + f' ; echo {M}\n')
        buf = b''
        end = time.time() + timeout
        while time.time() < end:
            if chan.recv_ready():
                r = chan.recv(65536)
                if r:
                    buf += r
                    if M.encode() in buf:
                        return
            else:
                time.sleep(0.05)

    # Multiple separate sends (each ~1 second apart)
    # First: clean + compile
    send_wait(f'cd {REMOTE} && rm -f {name}* && ibtool --compile {name}.nib {fn}', 30)
    # Use 1 ibtool command per send to be safe
    for cmd in [
        f'ibtool --classes {fn} > {name}_classes.plist',
        f'ibtool --objects {fn} > {name}_objects.plist',
        f'ibtool --hierarchy {fn} > {name}_hierarchy.plist',
        f'ibtool --connections {fn} > {name}_connections.plist',
        f'ibtool --all {fn} > {name}_all.plist',
        f'ibtool --version-history {fn} > {name}_version-history.plist',
        f'ibtool --localizable-strings {fn} > {name}_localizable-strings.plist',
        f'ibtool --localizable-all {fn} > {name}_localizable-all.plist',
        f'ibtool --localizable-geometry {fn} > {name}_localizable-geometry.plist',
        f'ibtool --localizable-stringarrays {fn} > {name}_localizable-stringarrays.plist',
        f'ibtool --localizable-other {fn} > {name}_localizable-other.plist',
        f'ibtool --localizable-to-many-relationships {fn} > {name}_localizable-to-many-relationships.plist',
        f'ibtool --warnings {fn} > {name}_warnings.plist',
        f'ibtool --errors {fn} > {name}_errors.plist',
        f'ibtool --notices {fn} > {name}_notices.plist',
        f'ibtool --export-xliff {name}.xlf --source-language en --target-language ja {fn}',
        f'ibtool --export-strings-file {name}.strings {fn}',
        f'ibtool --generate-strings-file {name}_gen.strings {fn}',
        f'ibtool --write {name}_out.xib {fn}',
        f'ibtool --upgrade --write {name}_up.xib {fn}',
        f'ibtool --remove-plugin-dependencies --write {name}_rpd.xib {fn}',
        f'ibtool --strip --compile {name}_strip.nib {fn}',
        f'ibtool --all --output-format binary1 {fn} > {name}_all.bin',
        f'ibtool --all --output-format human-readable-text {fn} > {name}_all.txt',
    ]:
        send_wait(f'cd {REMOTE} && {cmd}', 15)

    count = 0
    for fn2 in sftp.listdir(REMOTE):
        if fn2.startswith('.'):
            continue
        if not fn2.startswith(name + '.') and not fn2.startswith(name + '_'):
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
    for i in range(5):  # 5 個の sample を生成
        process(f'ios_{i}', XIB_IOS.replace('v1', f'v_{i}').replace('sa1', f'sa_{i}').replace('Bcu-3y-fUS', f'SA_{i}').replace('iN0-l3-epB', f'V_{i}'))


if __name__ == '__main__':
    main()
