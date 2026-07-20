#!/usr/bin/env python3
"""
harvest_v5.py - 本物の Apple ibtool 出力を大量取得する

Mac 上の新セッション (lYyOdmMKT7AYrCDUvuAd) で:
- 様々な xib / storyboard を /tmp に作る
- ibtool で全機能 (--compile, --export-strings-file, --export-xliff,
  --classes, --objects, --hierarchy, --all, --localizable-* 等) を実行
- sftp で取得
"""
import paramiko, time, os, sys, re, json

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = sys.argv[1] if len(sys.argv) > 1 else 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'

REMOTE = '/tmp/ibtool_probe'
LOCAL = '/home/user/ibtool-py/fixtures/probe'

# Various xib templates to test different platforms
XIB_TEMPLATES = {
    # iOS simple view
    'ios_view.xib': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="System colors in document resources" minToolsVersion="11.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
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
</document>''',

    # tvOS
    'tvos_view.xib': '''<?xml version="1.0" encoding="UTF-8"?>
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
            <color key="backgroundColor" red="0.0" green="0.0" blue="0.0" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
        </view>
    </objects>
</document>''',

    # macOS
    'macos_view.xib': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.Cocoa.XIB" version="3.0" toolsVersion="22154" targetRuntime="macOS.Cocoa" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="mac" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaPlugin" version="22131"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <objects>
        <window title="Window" allowsToolTipsWhenApplicationIsInactive="NO" autorecalculatesKeyViewLoop="NO" releasedWhenClosed="NO" visibleAtLaunch="NO" animationBehavior="default" id="QvC-M9-y7g">
            <windowStyleMask key="styleMask" titled="YES" closable="YES" miniaturizable="YES" resizable="YES"/>
            <windowPositionMask key="initialPositionMask" leftStrut="YES" rightStrut="YES" topStrut="YES" bottomStrut="YES"/>
            <rect key="contentRect" x="196" y="240" width="480" height="270"/>
            <rect key="screenRect" x="0.0" y="0.0" width="1440" height="900"/>
            <view key="contentView" wantsLayer="YES" id="EiT-Mj-1SZ">
                <rect key="frame" x="0.0" y="0.0" width="480" height="270"/>
                <autoresizingMask key="autoresizingMask"/>
            </view>
        </window>
        <customObject id="-1" userLabel="File's Owner" customClass="NSApplication"/>
    </objects>
</document>''',
}


def sftp_get(sftp, rp, lp):
    """Get one file"""
    try:
        sftp.get(rp, lp)
        return True
    except Exception as e:
        print(f'  ERR {rp}: {e}')
        return False


def sftp_put(sftp, lp, rp):
    """Put one file"""
    try:
        sftp.put(lp, rp)
        return True
    except Exception as e:
        print(f'  ERR put {lp}: {e}')
        return False


def run(chan, cmd, t=3):
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
    text = data.decode('utf-8', errors='replace')
    text = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)
    text = re.sub(r'\x1b\([AB]', '', text)
    text = re.sub(r'\x1b[\(\)][0-9A-Za-z]', '', text)
    text = re.sub(r'\x1b[\[\]()][0-9;?]*[A-Za-z]?', '', text)
    return text


def main():
    os.makedirs(LOCAL, exist_ok=True)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY)
    client.connect(HOST, port=PORT, username=USER, pkey=pkey,
                   allow_agent=False, look_for_keys=False, timeout=15)
    print(f'connected')

    sftp = client.open_sftp()
    chan = client.get_transport().open_session(timeout=15)
    chan.get_pty(term='xterm', width=132, height=43)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)
    print('shell ready')

    # Make remote workdir
    run(chan, f'mkdir -p {REMOTE}', 2)
    run(chan, f'rm -rf {REMOTE}/*', 2)

    # Upload templates via sftp
    print('--- uploading templates ---')
    for name, content in XIB_TEMPLATES.items():
        local_tmp = f'/tmp/{name}'
        with open(local_tmp, 'w') as f:
            f.write(content)
        sftp.put(local_tmp, f'{REMOTE}/{name}')
        print(f'  uploaded {name}')

    # Run ibtool on each
    print('--- running ibtool ---')
    for name in XIB_TEMPLATES:
        base = name.replace('.xib', '')
        # compile to nib
        run(chan, f'cd {REMOTE} && ibtool --compile {base}.nib {name} 2>&1', 4)
        # classes
        run(chan, f'cd {REMOTE} && ibtool --classes {name} > {base}_classes.plist 2>&1', 3)
        # objects
        run(chan, f'cd {REMOTE} && ibtool --objects {name} > {base}_objects.plist 2>&1', 3)
        # hierarchy
        run(chan, f'cd {REMOTE} && ibtool --hierarchy {name} > {base}_hierarchy.plist 2>&1', 3)
        # connections
        run(chan, f'cd {REMOTE} && ibtool --connections {name} > {base}_connections.plist 2>&1', 3)
        # all
        run(chan, f'cd {REMOTE} && ibtool --all {name} > {base}_all.plist 2>&1', 3)
        # version-history
        run(chan, f'cd {REMOTE} && ibtool --version-history {name} > {base}_vh.plist 2>&1', 2)
        # export-strings-file
        run(chan, f'cd {REMOTE} && ibtool --export-strings-file {base}.strings {name} 2>&1', 2)
        # generate-strings-file
        run(chan, f'cd {REMOTE} && ibtool --generate-strings-file {base}_gen.strings {name} 2>&1', 2)
        # localizable-strings
        run(chan, f'cd {REMOTE} && ibtool --localizable-strings {name} > {base}_locstr.plist 2>&1', 2)
        # export-xliff
        run(chan, f'cd {REMOTE} && ibtool --export-xliff {base}.xlf --source-language en --target-language ja {name} 2>&1', 3)
        # generate-xliff
        run(chan, f'cd {REMOTE} && ibtool --generate-xliff {base}_gen.xlf --source-language en --target-language ja {name} 2>&1', 3)
        # warnings
        run(chan, f'cd {REMOTE} && ibtool --warnings {name} > {base}_warn.plist 2>&1', 2)
        # errors
        run(chan, f'cd {REMOTE} && ibtool --errors {name} > {base}_err.plist 2>&1', 2)
        # notices
        run(chan, f'cd {REMOTE} && ibtool --notices {name} > {base}_notice.plist 2>&1', 2)
        # localizable-all
        run(chan, f'cd {REMOTE} && ibtool --localizable-all {name} > {base}_locall.plist 2>&1', 3)
        # human-readable-text
        run(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text {name} > {base}_all.txt 2>&1', 3)
        # binary1
        run(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 {name} > {base}_all.bin 2>&1', 3)
        # write (xib 書き出し)
        run(chan, f'cd {REMOTE} && ibtool --write {base}_out.xib {name} 2>&1', 2)
        # strip
        run(chan, f'cd {REMOTE} && ibtool --strip --compile {base}_strip.nib {name} 2>&1', 3)
        # upgrade
        run(chan, f'cd {REMOTE} && ibtool --upgrade --write {base}_up.xib {name} 2>&1', 2)
        print(f'  processed {name}')

    # List remote
    print('--- ls remote ---')
    print(run(chan, f'ls -la {REMOTE}', 2))

    # Get all files via sftp
    print('--- sftp get ---')
    items = sftp.listdir_attr(REMOTE)
    for item in items:
        if item.filename.startswith('.'):
            continue
        rp = f'{REMOTE}/{item.filename}'
        lp = f'{LOCAL}/{item.filename}'
        try:
            sftp.get(rp, lp)
            print(f'  got {item.filename}')
        except Exception as e:
            print(f'  ERR {item.filename}: {e}')

    sftp.close()
    chan.close()
    client.close()
    print('--- done ---')


if __name__ == '__main__':
    main()
