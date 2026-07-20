#!/usr/bin/env python3
"""harvest_v7: 1 platform = 1 SSH 接続 (毎回 bash 起動で send-keys ブロック回避)"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_v7'
LOCAL = '/home/user/ibtool-py/fixtures/probe_v7'


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


def run_batch(chan, batch, timeout=30):
    M = f'IBTOOL_END_{time.time_ns()}'
    chan.send(batch + f' ; echo {M}\n')
    buf = b''
    end = time.time() + timeout
    while time.time() < end:
        if chan.recv_ready():
            try:
                r = chan.recv(65536)
                if r:
                    buf += r
                    if M.encode() in buf:
                        return buf.decode('utf-8', errors='replace')
            except Exception:
                pass
        else:
            time.sleep(0.05)
    return buf.decode('utf-8', errors='replace')


def process(name, ext, content):
    print(f'  processing {name}{ext}...')
    client, sftp, chan = make_chan()
    with open(f'/tmp/{name}{ext}', 'w') as f:
        f.write(content)
    # mkdir first via sftp (parent must exist)
    try:
        sftp.mkdir(REMOTE)
    except IOError:
        pass  # already exists
    sftp.put(f'/tmp/{name}{ext}', f'{REMOTE}/{name}{ext}')

    out_ext = '.storyboardc' if ext == '.storyboard' else '.nib'
    cmds = []
    cmds.append(f'rm -rf {REMOTE}/*')
    cmds.append(f'ibtool --compile {name}{out_ext} {name}{ext}')
    for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                'localizable-to-many-relationships']:
        cmds.append(f'ibtool --{cmd} {name}{ext} > {name}_{cmd}.plist')
    cmds.append(f'ibtool --export-xliff {name}.xlf --source-language en --target-language ja {name}{ext}')
    cmds.append(f'ibtool --export-strings-file {name}.strings {name}{ext}')
    cmds.append(f'ibtool --generate-strings-file {name}_gen.strings {name}{ext}')
    cmds.append(f'ibtool --write {name}_out.xib {name}{ext}')
    cmds.append(f'ibtool --upgrade --write {name}_up.xib {name}{ext}')
    cmds.append(f'ibtool --remove-plugin-dependencies --write {name}_rpd.xib {name}{ext}')
    cmds.append(f'ibtool --strip --compile {name}_strip{out_ext} {name}{ext}')
    cmds.append(f'ibtool --all --output-format binary1 {name}{ext} > {name}_all.bin')
    cmds.append(f'ibtool --all --output-format human-readable-text {name}{ext} > {name}_all.txt')
    batch = f'cd {REMOTE} && ' + ' && '.join(cmds)
    out = run_batch(chan, batch, timeout=60)
    print(f'  batch output: {out[:500]}')

    # sftp get
    items = sftp.listdir(REMOTE)
    print(f'  remote files: {len(items)}: {items[:5]}')
    for fn in items:
        if fn.startswith('.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn}', f'{LOCAL}/{fn}')
        except Exception as e:
            print(f'  err {fn}: {e}')

    sftp.close()
    chan.close()
    client.close()
    print(f'  done {name}')


def main():
    os.makedirs(LOCAL, exist_ok=True)
    XIB_IOS = open('/home/user/ibtool-py/scripts/harvest_v6.py').read()  # hack: not real
    # Use simple templates
    templates = {
        'tvos': ('.xib', '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" variant="tvOS" propertyAccessControl="none" useAutolayout="YES">
<device id="apple_tv" orientation="landscape"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="iN0-l3-epB"><rect key="frame" x="0.0" y="0.0" width="1920" height="1080"/></view>
</objects>
</document>'''),
        'macos': ('.xib', '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.Cocoa.XIB" version="3.0" toolsVersion="22154" targetRuntime="macOS.Cocoa" propertyAccessControl="none" useAutolayout="YES">
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaPlugin" version="22131"/></dependencies>
<objects>
<window title="Test" id="QvC-M9-y7g"><windowStyleMask key="styleMask" titled="YES"/><rect key="contentRect" x="196" y="240" width="480" height="270"/>
<view key="contentView" id="EiT-Mj-1SZ"><rect key="frame" x="0.0" y="0.0" width="480" height="270"/><autoresizingMask key="autoresizingMask"/></view>
</window>
<customObject id="-1" userLabel="File's Owner" customClass="NSApplication"/>
</objects>
</document>'''),
        'xr': ('.xib', '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" variant="xrOS" propertyAccessControl="none" useAutolayout="YES">
<device id="xr" orientation="landscape"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="iN0-l3-epB"><rect key="frame" x="0.0" y="0.0" width="1280" height="720"/></view>
</objects>
</document>'''),
        'watch': ('.xib', '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.WatchKit.XIB" version="3.0" toolsVersion="22154" targetRuntime="watchKit" propertyAccessControl="none" useAutolayout="YES">
<device id="watch42"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.WatchKitPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<label alignment="center" id="Lbl-1"><rect key="frame" x="0" y="0" width="100" height="30"/></label>
</objects>
</document>'''),
        'story': ('.storyboard', '''<?xml version="1.0" encoding="UTF-8"?>
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
</document>'''),
    }
    for name, (ext, content) in templates.items():
        process(name, ext, content)


if __name__ == '__main__':
    main()
