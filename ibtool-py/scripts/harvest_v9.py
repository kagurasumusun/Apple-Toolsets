#!/usr/bin/env python3
"""harvest_v9: 多彩な iOS フィクスチャ大量取得

10 種類の異なる iOS xib + 接続・outlet・action・constraint を含む本格的なサンプルで
ibtool の全機能出力を集める
"""
import paramiko, time, os, sys, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'
REMOTE = '/tmp/ibtool_v9'
LOCAL = '/home/user/ibtool-py/fixtures/probe_v9'

# 各サンプル xib
SAMPLES = {
    # 0. シンプル view
    'simple': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
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

    # 1. ボタン・ラベル付き
    'button': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner">
            <connections>
                <outlet property="view" destination="iN0-l3-epB" id="owner-view"/>
                <outlet property="label" destination="LBL-1" id="owner-label"/>
                <outlet property="button" destination="BTN-1" id="owner-button"/>
            </connections>
        </placeholder>
        <placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
        <view contentMode="scaleToFill" id="iN0-l3-epB">
            <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
            <subviews>
                <label opaque="NO" userInteractionEnabled="NO" contentMode="left" horizontalHuggingPriority="251" verticalHuggingPriority="251" text="Hello" textAlignment="center" lineBreakMode="tailTruncation" baselineAdjustment="alignBaselines" adjustsFontSizeToFit="NO" translatesAutoresizingMaskIntoConstraints="NO" id="LBL-1">
                    <rect key="frame" x="20" y="40" width="335" height="21"/>
                    <fontDescription key="fontDescription" type="system" pointSize="17"/>
                    <nil key="textColor"/>
                    <nil key="highlightedColor"/>
                </label>
                <button opaque="NO" contentMode="scaleToFill" contentHorizontalAlignment="center" contentVerticalAlignment="center" buttonType="system" lineBreakMode="middleTruncation" translatesAutoresizingMaskIntoConstraints="NO" id="BTN-1">
                    <rect key="frame" x="20" y="80" width="100" height="44"/>
                    <state key="normal" title="Tap me"/>
                    <connections>
                        <action selector="buttonTapped:" destination="-1" eventType="touchUpInside" id="btn-tap"/>
                    </connections>
                </button>
            </subviews>
            <viewLayoutGuide key="safeArea" id="Bcu-3y-fUS"/>
            <color key="backgroundColor" systemColor="systemBackgroundColor"/>
            <constraints>
                <constraint firstItem="LBL-1" firstAttribute="top" secondItem="Bcu-3y-fUS" secondAttribute="top" constant="20" id="LBL-top"/>
                <constraint firstItem="LBL-1" firstAttribute="leading" secondItem="Bcu-3y-fUS" secondAttribute="leading" constant="20" id="LBL-lead"/>
                <constraint firstAttribute="trailing" secondItem="LBL-1" secondAttribute="trailing" constant="20" id="LBL-trail"/>
                <constraint firstItem="BTN-1" firstAttribute="top" secondItem="LBL-1" secondAttribute="bottom" constant="20" id="BTN-top"/>
                <constraint firstItem="BTN-1" firstAttribute="leading" secondItem="Bcu-3y-fUS" secondAttribute="leading" constant="20" id="BTN-lead"/>
            </constraints>
        </view>
    </objects>
    <resources>
        <systemColor name="systemBackgroundColor">
            <color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
        </systemColor>
    </resources>
</document>''',

    # 2. 複数 subview + ネスト
    'nested': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
        <view contentMode="scaleToFill" id="iN0-l3-epB">
            <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
            <subviews>
                <view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="INNER-1">
                    <rect key="frame" x="20" y="40" width="335" height="100"/>
                    <color key="backgroundColor" red="0.5" green="0.5" blue="0.5" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                    <subviews>
                        <label opaque="NO" userInteractionEnabled="NO" contentMode="left" text="Inner" textAlignment="center" translatesAutoresizingMaskIntoConstraints="NO" id="INNER-LBL">
                            <rect key="frame" x="10" y="10" width="315" height="20"/>
                            <fontDescription key="fontDescription" type="system" pointSize="14"/>
                        </label>
                    </subviews>
                </view>
            </subviews>
            <viewLayoutGuide key="safeArea" id="Bcu-3y-fUS"/>
            <color key="backgroundColor" white="1" alpha="1" colorSpace="custom" customColorSpace="genericGamma22GrayColorSpace"/>
        </view>
    </objects>
</document>''',

    # 3. カスタム class
    'customclass': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" customClass="MyViewController" sceneMemberID="filesOwner"/>
        <placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
        <view contentMode="scaleToFill" id="iN0-l3-epB" customClass="MyView">
            <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
        </view>
    </objects>
</document>''',

    # 4. table view
    'table': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner">
            <connections>
                <outlet property="dataSource" destination="-1" id="ds"/>
                <outlet property="delegate" destination="-1" id="dlg"/>
                <outlet property="tableView" destination="TV-1" id="tv-out"/>
            </connections>
        </placeholder>
        <placeholder placeholderIdentifier="IBFirstResponder" id="-2" customClass="UIResponder" sceneMemberID="firstResponder"/>
        <tableView clipsSubviews="YES" contentMode="scaleToFill" alwaysBounceVertical="YES" dataMode="prototypes" style="plain" separatorStyle="default" rowHeight="-1" sectionHeaderHeight="22" sectionFooterHeight="22" translatesAutoresizingMaskIntoConstraints="NO" id="TV-1">
            <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            <color key="backgroundColor" systemColor="systemBackgroundColor"/>
            <prototypes>
                <tableViewCell clipsSubviews="YES" contentMode="scaleToFill" preservesSuperviewLayoutMargins="YES" selectionStyle="default" indentationWidth="10" reuseIdentifier="Cell" id="TVC-1">
                    <rect key="frame" x="0.0" y="0.0" width="375" height="44"/>
                    <autoresizingMask key="autoresizingMask"/>
                    <tableViewCellContentView key="contentView" opaque="NO" clipsSubviews="YES" multipleTouchEnabled="YES" contentMode="center" preservesSuperviewLayoutMargins="YES" insetsLayoutMarginsFromSafeArea="NO" tableViewCell="TVC-1" id="TVC-1-c">
                        <rect key="frame" x="0.0" y="0.0" width="375" height="44"/>
                    </tableViewCellContentView>
                </tableViewCell>
            </prototypes>
        </tableView>
    </objects>
    <resources>
        <systemColor name="systemBackgroundColor">
            <color red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
        </systemColor>
    </resources>
</document>''',

    # 5. collection view
    'coll': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <collectionView clipsSubviews="YES" multipleTouchEnabled="YES" contentMode="scaleToFill" dataMode="prototypes" translatesAutoresizingMaskIntoConstraints="NO" id="CV-1">
            <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            <collectionViewFlowLayout key="collectionViewLayout" minimumLineSpacing="10" minimumInteritemSpacing="10" id="CVL-1">
                <size key="itemSize" width="100" height="100"/>
            </collectionViewFlowLayout>
            <cells>
                <collectionViewCell opaque="NO" clipsSubviews="YES" multipleTouchEnabled="YES" contentMode="center" id="CVC-1">
                    <rect key="frame" x="0.0" y="0.0" width="100" height="100"/>
                    <autoresizingMask key="autoresizingMask"/>
                </collectionViewCell>
            </cells>
        </collectionView>
    </objects>
</document>''',

    # 6. stack view
    'stack': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <stackView opaque="NO" contentMode="scaleToFill" axis="vertical" alignment="fill" spacing="10" translatesAutoresizingMaskIntoConstraints="NO" id="SV-1">
            <rect key="frame" x="20" y="40" width="335" height="200"/>
            <subviews>
                <view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="SV-1-1">
                    <rect key="frame" x="0.0" y="0.0" width="335" height="50"/>
                    <color key="backgroundColor" red="1" green="0" blue="0" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                </view>
                <view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="SV-1-2">
                    <rect key="frame" x="0.0" y="60" width="335" height="50"/>
                    <color key="backgroundColor" red="0" green="1" blue="0" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                </view>
                <view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="SV-1-3">
                    <rect key="frame" x="0.0" y="120" width="335" height="50"/>
                    <color key="backgroundColor" red="0" green="0" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                </view>
            </subviews>
        </stackView>
    </objects>
</document>''',

    # 7. スクロールビュー
    'scroll': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <scrollView clipsSubviews="YES" multipleTouchEnabled="YES" contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="SCV-1">
            <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            <subviews>
                <view contentMode="scaleToFill" translatesAutoresizingMaskIntoConstraints="NO" id="SCV-1-c">
                    <rect key="frame" x="0.0" y="0.0" width="375" height="1000"/>
                    <color key="backgroundColor" red="0.9" green="0.9" blue="0.9" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                </view>
            </subviews>
        </scrollView>
    </objects>
</document>''',

    # 8. navigation + tabbar
    'navtab': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <tabBarController id="TBC-1" sceneMemberID="viewController">
            <tabBar key="tabBar" contentMode="scaleToFill" id="TB-1"/>
            <connections>
                <segue destination="VC-1" kind="relationship" relationship="viewControllers" id="seg1"/>
                <segue destination="VC-2" kind="relationship" relationship="viewControllers" id="seg2"/>
            </connections>
        </tabBarController>
        <viewController id="VC-1" customClass="FirstViewController" sceneMemberID="viewController">
            <view key="view" contentMode="scaleToFill" id="VC-1-v">
                <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            </view>
            <navigationItem key="navigationItem" title="First" id="VC-1-ni"/>
        </viewController>
        <viewController id="VC-2" customClass="SecondViewController" sceneMemberID="viewController">
            <view key="view" contentMode="scaleToFill" id="VC-2-v">
                <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
            </view>
        </viewController>
    </objects>
</document>''',

    # 9. イメージアセット付き
    'image': '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
    </dependencies>
    <objects>
        <placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
        <imageView userInteractionEnabled="NO" contentMode="scaleAspectFit" horizontalHuggingPriority="251" verticalHuggingPriority="251" image="logo" translatesAutoresizingMaskIntoConstraints="NO" id="IV-1">
            <rect key="frame" x="50" y="100" width="275" height="200"/>
        </imageView>
    </objects>
    <resources>
        <image name="logo" width="100" height="100"/>
    </resources>
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
    chan.get_pty(term='dumb', width=200, height=50)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)
    # Disable line editing completions to prevent file name completion interference
    chan.send("bind 'set disable-completion on' 2>/dev/null; export PS1='READY>'\n")
    time.sleep(0.5)
    while chan.recv_ready():
        chan.recv(65536)
    return client, sftp, chan


def run_one(chan, cmd, timeout=8):
    M = f'IBEND{time.time_ns() % 1000000:06d}'
    chan.send(cmd + f' ; echo {M}\n')
    buf = b''
    end = time.time() + timeout
    while time.time() < end:
        if chan.recv_ready():
            try:
                r = chan.recv(65536)
                if r:
                    buf += r
                    if M.encode() in buf:
                        idx = buf.find(M.encode())
                        out = buf[:idx].decode('utf-8', errors='replace')
                        out = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', out)
                        out = re.sub(r'\x1b[\(\)][0-9A-Za-z]', '', out)
                        out = re.sub(r'\x1b[\[\]()][0-9;?]*[A-Za-z]?', '', out)
                        out = re.sub(r'\r', '', out)
                        return out
            except Exception:
                pass
        else:
            time.sleep(0.05)
    return buf.decode('utf-8', errors='replace')


def process(name, content, sftp, chan):
    print(f'  {name}...')
    fn = f'{name}.xib'
    with open(f'/tmp/{fn}', 'w') as f:
        f.write(content)
    sftp.put(f'/tmp/{fn}', f'{REMOTE}/{fn}')

    # Delete previous outputs (NOT the source xib)
    run_one(chan, f'cd {REMOTE} && rm -f {name}.nib {name}_*.plist {name}.xlf {name}.strings {name}_gen.strings {name}_*.xib {name}_*.bin {name}_*.txt {name}_strip.nib', 2)
    run_one(chan, f'cd {REMOTE} && ibtool --compile {name}.nib {fn}', 8)
    for cmd in ['classes', 'objects', 'hierarchy', 'connections', 'all', 'version-history',
                'localizable-strings', 'localizable-all', 'warnings', 'errors', 'notices',
                'localizable-geometry', 'localizable-stringarrays', 'localizable-other',
                'localizable-to-many-relationships']:
        run_one(chan, f'cd {REMOTE} && ibtool --{cmd} {fn} > {name}_{cmd}.plist', 6)
    run_one(chan, f'cd {REMOTE} && ibtool --export-xliff {name}.xlf --source-language en --target-language ja {fn}', 6)
    run_one(chan, f'cd {REMOTE} && ibtool --export-strings-file {name}.strings {fn}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --generate-strings-file {name}_gen.strings {fn}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --write {name}_out.xib {fn}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --upgrade --write {name}_up.xib {fn}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --remove-plugin-dependencies --write {name}_rpd.xib {fn}', 4)
    run_one(chan, f'cd {REMOTE} && ibtool --strip --compile {name}_strip.nib {fn}', 6)
    run_one(chan, f'cd {REMOTE} && ibtool --all --output-format binary1 {fn} > {name}_all.bin', 6)
    run_one(chan, f'cd {REMOTE} && ibtool --all --output-format human-readable-text {fn} > {name}_all.txt', 6)

    for fn2 in sftp.listdir(REMOTE):
        if fn2.startswith('.'):
            continue
        if not fn2.startswith(name + '.'):
            continue
        try:
            sftp.get(f'{REMOTE}/{fn2}', f'{LOCAL}/{fn2}')
        except Exception as e:
            pass  # directory


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
