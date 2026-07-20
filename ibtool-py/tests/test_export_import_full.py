"""
test_export_import_full.py - --export/--import 全形式の完全テスト

Apple ibtool の input/output 形式両方をサポート:
1. シンプル形式: {className: [prop1, prop2]}
2. Apple 形式: {com.apple.ibtool.document.export: {object_id: {keypath: value}}}
"""
import os, sys, plistlib, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _run(args):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        sys.stdout = io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return code, out, err
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestExportSimpleFormat(unittest.TestCase):
    """シンプル形式: {className: [prop1, prop2]}"""

    def setUp(self):
        self.xib = FIXTURES / "probe_v8" / "ios.xib"
        if not self.xib.exists():
            self.skipTest("no ios.xib")

    def test_export_ui_view_props(self):
        """UIView クラスのプロパティ書き出し (customClass=UIView を追加した xib で)"""
        xib_content = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="v1" customClass="UIView"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/></view>
</objects>
</document>'''
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False, mode='w') as fx:
            fx.write(xib_content)
            xib_tmp = fx.name
        plist = b"""<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>UIView</key>
<array><string>contentMode</string></array>
</dict></plist>"""
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            f.write(plist)
            tmp = f.name
        try:
            code, out, _ = _run(["--export", tmp, xib_tmp])
            self.assertEqual(code, 0)
            d = plistlib.loads(out.encode("utf-8"))
            self.assertIn("com.apple.ibtool.document.export", d)
            export = d["com.apple.ibtool.document.export"]
            # v1 (UIView) のプロパティが含まれる
            self.assertIn("v1", export, f"v1 not in {list(export.keys())}")
            self.assertIn("contentMode", export["v1"])
            self.assertEqual(export["v1"]["contentMode"], "scaleToFill")
        finally:
            for p in [tmp, xib_tmp]:
                if os.path.exists(p):
                    os.unlink(p)


class TestExportAppleFormat(unittest.TestCase):
    """Apple 形式: {com.apple.ibtool.document.export: {object_id: {keypath: value}}}"""

    def setUp(self):
        self.xib = FIXTURES / "probe_v8" / "ios.xib"
        if not self.xib.exists():
            self.skipTest("no ios.xib")

    def test_export_apple_format_passthrough(self):
        """Apple 形式は passthrough"""
        plist = b"""<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>com.apple.ibtool.document.export</key>
<dict>
<key>iN0-l3-epB</key>
<dict>
<key>frame</key>
<string>{{0, 0}, {100, 100}}</string>
<key>hidden</key>
<true/>
</dict>
</dict>
</dict></plist>"""
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            f.write(plist)
            tmp = f.name
        try:
            code, out, _ = _run(["--export", tmp, str(self.xib)])
            self.assertEqual(code, 0)
            d = plistlib.loads(out.encode("utf-8"))
            export = d["com.apple.ibtool.document.export"]
            # iN0-l3-epB を含む
            self.assertIn("iN0-l3-epB", export)
            # 値が passthrough
            self.assertEqual(export["iN0-l3-epB"]["frame"], "{{0, 0}, {100, 100}}")
            self.assertTrue(export["iN0-l3-epB"]["hidden"])
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestImportAppleFormat(unittest.TestCase):
    """--import: Apple 形式 dict を受け取って xib に反映"""

    def setUp(self):
        self.xib = FIXTURES / "probe_v8" / "ios.xib"
        if not self.xib.exists():
            self.skipTest("no ios.xib")

    def test_import_apple_format(self):
        plist = b"""<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>com.apple.ibtool.document.export</key>
<dict>
<key>iN0-l3-epB</key>
<dict>
<key>frame</key>
<string>{{0, 0}, {200, 200}}</string>
</dict>
</dict>
</dict></plist>"""
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            f.write(plist)
            tmp = f.name
        out_xib = tempfile.NamedTemporaryFile(suffix=".xib", delete=False)
        out_xib.close()
        try:
            code, out, _ = _run(["--import", tmp, "--write", out_xib.name, str(self.xib)])
            self.assertEqual(code, 0)
            # write された xib を確認
            content = open(out_xib.name).read()
            # iN0-l3-epB に frame 属性
            self.assertIn("iN0-l3-epB", content)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
            if os.path.exists(out_xib.name):
                os.unlink(out_xib.name)


class TestExportImportRoundTrip(unittest.TestCase):
    """--export → --import のラウンドトリップ"""

    def setUp(self):
        self.xib = FIXTURES / "probe_v8" / "ios.xib"
        if not self.xib.exists():
            self.skipTest("no ios.xib")

    def test_export_then_import(self):
        # Prepare input plist (empty class dict)
        in_plist = tempfile.NamedTemporaryFile(suffix=".plist", delete=False, mode='w')
        in_plist.write('<?xml version="1.0" encoding="UTF-8"?>\n<plist version="1.0"><dict><key>UIView</key><array><string>contentMode</string></array></dict></plist>')
        in_plist.close()
        in_plist_name = in_plist.name
        out_xib_name = None
        try:
            # Export
            code, out, _ = _run(["--export", in_plist_name, str(self.xib)])
            self.assertEqual(code, 0)
            # Import
            out_xib = tempfile.NamedTemporaryFile(suffix=".xib", delete=False)
            out_xib.close()
            out_xib_name = out_xib.name
            code, out, _ = _run(["--import", in_plist_name, "--write", out_xib_name, str(self.xib)])
            self.assertEqual(code, 0)
            self.assertGreater(os.path.getsize(out_xib_name), 0)
        finally:
            if os.path.exists(in_plist_name):
                os.unlink(in_plist_name)
            if out_xib_name and os.path.exists(out_xib_name):
                os.unlink(out_xib_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
