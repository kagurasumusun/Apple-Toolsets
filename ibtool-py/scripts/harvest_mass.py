#!/usr/bin/env python3
"""harvest_mass: 大量の本物 Apple ibtool フィクスチャ取得

接続が復活したので、step1 方式 (1 接続 = 1 コマンド)で 10 種類 xib を 1 つずつ
取得する。各接続は sftp 完全動作 + bash 1 send のみ。
"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_mass'
LOCAL = '/home/user/ibtool-py/fixtures/mass'

# 10 種類の iOS xib サンプル
SAMPLES = {
    'simple': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
<view contentMode="scaleToFill" id="v1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/><viewLayoutGuide key="safeArea" id="sa1"/><color key="backgroundColor" systemColor="bg"/></view>
</objects>
<resources><systemColor name="bg"><color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/></systemColor></resources>
</document>''',

    'button': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"><connections><outlet property="view" destination="v1" id="o1"/></connections></placeholder>
<placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
<view contentMode="scaleToFill" id="v1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/><subviews><button opaque="NO" contentMode="scaleToFill" contentHorizontalAlignment="center" contentVerticalAlignment="center" buttonType="system" translatesAutoresizingMaskIntoConstraints="NO" id="b1"><rect key="frame" x="20" y="80" width="100" height="44"/><state key="normal" title="Go"/><connections><action selector="btn:" destination="-1" eventType="touchUpInside" id="ac1"/></connections></button></subviews><viewLayoutGuide key="safeArea" id="sa1"/><color key="backgroundColor" white="1" alpha="1" colorSpace="custom" customColorSpace="genericGamma22GrayColorSpace"/></view>
</objects>
</document>''',

    'navtab': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<tabBarController id="tbc1" sceneMemberID="viewController"><tabBar key="tabBar" contentMode="scaleToFill" id="tb1"/><connections><segue destination="vc1" kind="relationship" relationship="viewControllers" id="s1"/></connections></tabBarController>
<viewController id="vc1" customClass="V1" sceneMemberID="viewController"><view key="view" contentMode="scaleToFill" id="vc1v"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/></view><navigationItem key="navigationItem" title="One" id="ni1"/></viewController>
</objects>
</document>''',

    'table': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"><connections><outlet property="tableView" destination="t1" id="o1"/></connections></placeholder>
<tableView clipsSubviews="YES" contentMode="scaleToFill" alwaysBounceVertical="YES" dataMode="prototypes" style="plain" rowHeight="44" sectionHeaderHeight="22" sectionFooterHeight="22" translatesAutoresizingMaskIntoConstraints="NO" id="t1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><prototypes><tableViewCell clipsSubviews="YES" contentMode="scaleToFill" preservesSuperviewLayoutMargins="YES" selectionStyle="default" reuseIdentifier="C" id="c1"><rect key="frame" x="0.0" y="0.0" width="375" height="44"/><tableViewCellContentView key="contentView" opaque="NO" clipsSubviews="YES" contentMode="center" id="c1c"><rect key="frame" x="0.0" y="0.0" width="375" height="44"/></tableViewCellContentView></tableViewCell></prototypes></tableView>
</objects>
</document>''',

    'coll': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<collectionView clipsSubviews="YES" contentMode="scaleToFill" dataMode="prototypes" translatesAutoresizingMaskIntoConstraints="NO" id="cv1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><collectionViewFlowLayout key="collectionViewLayout" minimumLineSpacing="10" minimumInteritemSpacing="10" id="cvl1"><size key="itemSize" width="100" height="100"/></collectionViewFlowLayout><cells><collectionViewCell opaque="NO" clipsSubviews="YES" contentMode="center" id="cvc1"><rect key="frame" x="0.0" y="0.0" width="100" height="100"/></collectionViewCell></cells></collectionView>
</objects>
</document>''',

    'stack': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<stackView opaque="NO" contentMode="scaleToFill" axis="vertical" alignment="fill" spacing="10" translatesAutoresizingMaskIntoConstraints="NO" id="sv1"><rect key="frame" x="20" y="40" width="335" height="200"/><subviews><view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="svv1"><rect key="frame" x="0.0" y="0.0" width="335" height="50"/><color key="backgroundColor" red="1" green="0" blue="0" alpha="1" colorSpace="custom" customColorSpace="sRGB"/></view><view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="svv2"><rect key="frame" x="0.0" y="60" width="335" height="50"/><color key="backgroundColor" red="0" green="1" blue="0" alpha="1" colorSpace="custom" customColorSpace="sRGB"/></view></subviews></stackView>
</objects>
</document>''',

    'customclass': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" customClass="MyVC" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="v1" customClass="MyView"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/></view>
</objects>
</document>''',

    'image': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<imageView userInteractionEnabled="NO" contentMode="scaleAspectFit" image="logo" translatesAutoresizingMaskIntoConstraints="NO" id="iv1"><rect key="frame" x="50" y="100" width="275" height="200"/></imageView>
</objects>
<resources><image name="logo" width="100" height="100"/></resources>
</document>''',

    'story': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" initialViewController="vc1">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<scenes>
<scene sceneID="s1"><objects><viewController id="vc1" customClass="VC1" sceneMemberID="viewController"><view key="view" contentMode="scaleToFill" id="vc1v"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/></view></viewController><placeholder placeholderIdentifier="IBFirstResponder" id="fr1" sceneMemberID="firstResponder"/></objects><point key="canvasLocation" x="50" y="50"/></scene>
</scenes>
</document>''',

    'nested': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="outer"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/><subviews><view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="inner"><rect key="frame" x="20" y="40" width="335" height="100"/><color key="backgroundColor" red="0.5" green="0.5" blue="0.5" alpha="1" colorSpace="custom" customColorSpace="sRGB"/><subviews><label opaque="NO" userInteractionEnabled="NO" contentMode="left" text="Inner" textAlignment="center" translatesAutoresizingMaskIntoConstraints="NO" id="innerLbl"><rect key="frame" x="10" y="10" width="315" height="20"/><fontDescription key="fontDescription" type="system" pointSize="14"/></label></subviews></view></subviews></view>
</objects>
</document>''',
}


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


def run_one(chan, cmd, timeout=4):
    chan.send(cmd + '\n')
    end = time.time() + timeout
    data = b''
    while time.time() < end:
        if chan.recv_ready():
            try:
                r = chan.recv(65536)
                if r:
                    data += r
                    # continue reading
            except Exception:
                break
        else:
            time.sleep(0.02)
    return data.decode('utf-8', errors='replace')


def process(name, content, sftp, chan):
    print(f'  {name}...')
    fn = f'{name}.xib' if name != 'story' else 'story.storyboard'
    localp = f'/tmp/{fn}'
    with open(localp, 'w') as f:
        f.write(content)
    sftp.put(localp, f'{REMOTE}/{fn}')

    out_ext = '.storyboardc' if name == 'story' else '.nib'

    # Verify upload
    items = sftp.listdir(REMOTE)
    if fn not in items:
        print(f'    upload failed for {fn}')
        return

    # Clean previous outputs (NOT source)
    run_one(chan, f'cd {REMOTE} && rm -f {name}.nib {name}*.nib {name}_*.plist {name}.xlf {name}.strings {name}_gen.strings {name}_*.xib {name}_*.bin {name}_*.txt', 2)

    # compile
    run_one(chan, f'cd {REMOTE} && ibtool --compile {name}{out_ext} {fn}', 4)
    # plist dumps
    for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                'localizable-to-many-relationships']:
        run_one(chan, f'cd {REMOTE} && ibtool --{cmd} {fn} > {name}_{cmd}.plist', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --export-xliff {name}.xlf --source-language en --target-language ja {fn}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --export-strings-file {name}.strings {fn}', 2)
    run_one(chan, f'cd {REMOTE} && ibtool --generate-strings-file {name}_gen.strings {fn}', 2)
    run_one(chan, f'cd {REMOTE} && ibtool --write {name}_out.xib {fn}', 2)
    run_one(chan, f'cd {REMOTE} && ibtool --upgrade --write {name}_up.xib {fn}', 2)
    run_one(chan, f'cd {REMOTE} && ibtool --remove-plugin-dependencies --write {name}_rpd.xib {fn}', 2)
    run_one(chan, f'cd {REMOTE} && ibtool --strip --compile {name}_strip{out_ext} {fn}', 3)
    run_one(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 {fn} > {name}_all.bin', 3)
    run_one(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text {fn} > {name}_all.txt', 3)

    for fn2 in sftp.listdir(REMOTE):
        if fn2.startswith('.') or not fn2.startswith(name + '.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn2}', f'{LOCAL}/{fn2}')
        except Exception:
            pass


def main():
    os.makedirs(LOCAL, exist_ok=True)
    client, sftp, chan = make_chan()
    try:
        sftp.mkdir(REMOTE)
    except IOError:
        pass
    for name, content in SAMPLES.items():
        process(name, content, sftp, chan)
    sftp.close()
    chan.close()
    client.close()


if __name__ == '__main__':
    main()
