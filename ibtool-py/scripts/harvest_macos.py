#!/usr/bin/env python3
"""harvest_macos: macOS xib の全フィクスチャ取得 (Mac SDK 必要)"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = '0z6pfERbIkK3HRrW097T'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/hmac'
LOCAL = '/home/user/ibtool-py/fixtures/mac'

XIB = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.Cocoa.XIB" version="3.0" toolsVersion="22154" targetRuntime="macOS.Cocoa" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="mac" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaPlugin" version="22131"/></dependencies>
<objects>
<window title="Test" id="w1"><windowStyleMask key="styleMask" titled="YES" closable="YES" miniaturizable="YES" resizable="YES"/><windowPositionMask key="initialPositionMask" leftStrut="YES" rightStrut="YES" topStrut="YES" bottomStrut="YES"/><rect key="contentRect" x="196" y="240" width="480" height="270"/><rect key="screenRect" x="0.0" y="0.0" width="1440" height="900"/><view key="contentView" wantsLayer="YES" id="cv1"><rect key="frame" x="0.0" y="0.0" width="480" height="270"/><autoresizingMask key="autoresizingMask"/></view></window>
<customObject id="-1" userLabel="File's Owner" customClass="NSApplication"/>
</objects>
</document>'''


def process():
    print('macOS...')
    fn = 'macos.xib'
    localp = f'/tmp/{fn}'
    with open(localp, 'w') as f:
        f.write(XIB)

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
    try:
        sftp.put(localp, f'{REMOTE}/{fn}')
        print(f'  uploaded: {REMOTE}/{fn}')
    except Exception as e:
        print(f'  UPLOAD FAIL: {e}')
        sftp.close()
        chan.close()
        client.close()
        return
    # Verify upload
    items = sftp.listdir(REMOTE)
    if fn not in items:
        print(f'  upload missing: {fn} in {items}')
        sftp.close()
        chan.close()
        client.close()
        return

    chan = client.get_transport().open_session(timeout=15)
    chan.get_pty(term='xterm', width=200, height=50)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)

    parts = [f"cd {REMOTE}", "rm -f macos*",
             "ibtool --compile macos.nib macos.xib"]
    for c in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
              'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
              'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
              'localizable-to-many-relationships']:
        parts.append(f"ibtool --{c} macos.xib > macos_{c}.plist")
    parts.append("ibtool --export-xliff macos.xlf --source-language en --target-language ja macos.xib")
    parts.append("ibtool --export-strings-file macos.strings macos.xib")
    parts.append("ibtool --generate-strings-file macos_gen.strings macos.xib")
    parts.append("ibtool --write macos_out.xib macos.xib")
    parts.append("ibtool --upgrade --write macos_up.xib macos.xib")
    parts.append("ibtool --remove-plugin-dependencies --write macos_rpd.xib macos.xib")
    parts.append("ibtool --strip --compile macos_strip.nib macos.xib")
    parts.append("ibtool --all --output-format binary1 macos.xib > macos_all.bin")
    parts.append("ibtool --all --output-format human-readable-text macos.xib > macos_all.txt")
    parts.append('echo IBLT_MAC')

    big = ' ; '.join(parts)
    chan.send(big + '\n')
    M = 'IBLT_MAC'
    buf = b''
    end = time.time() + 30
    while time.time() < end:
        if chan.recv_ready():
            r = chan.recv(65536)
            if r:
                buf += r
                if M.encode() in buf:
                    break
        else:
            time.sleep(0.02)

    count = 0
    for fn2 in sftp.listdir(REMOTE):
        if fn2.startswith('.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn2}', f'{LOCAL}/{fn2}')
            count += 1
        except Exception:
            pass
    print(f'  {count} files')

    sftp.close()
    chan.close()
    client.close()


def main():
    os.makedirs(LOCAL, exist_ok=True)
    process()


if __name__ == '__main__':
    main()
