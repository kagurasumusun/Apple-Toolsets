"""
test_strings_format.py - .strings ファイル出力の Apple 互換性検証

Apple ibtool --export-strings-file 出力:
  - UTF-16 LE with BOM
  - "object_id.key" = "value"; 形式
  - 各エントリは改行区切り
  - 末尾に改行

本実装の出力形式が Apple と一致するか検証。
"""
import os, sys, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool

XIB_WITH_STRINGS = '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES">
<device id="retina6_12" orientation="portrait"/>
<dependencies><plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/></dependencies>
<objects>
<placeholder placeholderIdentifier="IBFilesOwner" id="-1" userLabel="File's Owner" sceneMemberID="filesOwner"/>
<view contentMode="scaleToFill" id="v1"><rect key="frame" x="0.0" y="0.0" width="375" height="667"/><autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/><subviews>
<button opaque="NO" contentMode="scaleToFill" contentHorizontalAlignment="center" contentVerticalAlignment="center" buttonType="system" translatesAutoresizingMaskIntoConstraints="NO" id="b1"><rect key="frame" x="20" y="80" width="100" height="44"/><state key="normal" title="Hello World"/></button>
<label opaque="NO" userInteractionEnabled="NO" contentMode="left" text="My Label" textAlignment="center" translatesAutoresizingMaskIntoConstraints="NO" id="L1"><rect key="frame" x="20" y="40" width="335" height="21"/></label>
</subviews></view>
</objects>
</document>'''


def _run(args):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        sys.stdout = io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        return code, out
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestStringsFormat(unittest.TestCase):
    def setUp(self):
        self.xib_tmp = tempfile.NamedTemporaryFile(suffix=".xib", delete=False, mode="w", encoding="utf-8")
        self.xib_tmp.write(XIB_WITH_STRINGS)
        self.xib_tmp.close()
        self.str_tmp = tempfile.NamedTemporaryFile(suffix=".strings", delete=False)
        self.str_tmp.close()

    def tearDown(self):
        for p in [self.xib_tmp.name, self.str_tmp.name]:
            if os.path.exists(p):
                os.unlink(p)

    def test_export_strings_format(self):
        """--export-strings-file の出力形式"""
        code, _ = _run(["--export-strings-file", self.str_tmp.name, self.xib_tmp.name])
        self.assertEqual(code, 0)
        with open(self.str_tmp.name, "rb") as f: raw = f.read()
        # Apple 形式: "key" = "value"; 改行
        text = raw.decode("utf-8", errors="replace")
        # Hello World と My Label が含まれる
        self.assertIn("Hello World", text)
        self.assertIn("My Label", text)
        # 形式: "key" = "value";
        self.assertIn('" = "', text)
        self.assertTrue(text.endswith(";\n") or text.endswith(";"))

    def test_export_strings_apple_keys_format(self):
        """key は "object_id.prop" 形式"""
        code, _ = _run(["--export-strings-file", self.str_tmp.name, self.xib_tmp.name])
        with open(self.str_tmp.name, "rb") as f: raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        # "v1.title" = "Hello World"; のような Apple 形式
        self.assertIn('"v1.', text)
        self.assertIn('.title"', text)

    def test_export_strings_vs_apple(self):
        """pyibtool 出力 vs Apple 出力 (probe_v8)"""
        apple = Path(__file__).parent.parent / "fixtures" / "probe_v8" / "ios.strings"
        if not apple.exists():
            self.skipTest("no apple strings fixture")
        apple_raw = apple.read_bytes()
        # Apple 出力も " を含むなら両者の形式を比較
        code, _ = _run(["--export-strings-file", self.str_tmp.name, self.xib_tmp.name])
        with open(self.str_tmp.name, "rb") as f:
            py_raw = f.read()
        # 両者とも "key" = "value"; 形式
        if b'"' in apple_raw and b'"' in py_raw:
            apple_text = apple_raw.decode("utf-8", errors="replace")
            py_text = py_raw.decode("utf-8", errors="replace")
            # Apple は "key" = "value"; 形式
            self.assertIn('" = "', apple_text)
            self.assertIn('" = "', py_text)

    def test_generate_strings_empty_values(self):
        """--generate-strings-file は空値で生成"""
        gen_tmp = tempfile.NamedTemporaryFile(suffix=".strings", delete=False)
        gen_tmp.close()
        try:
            code, _ = _run(["--generate-strings-file", gen_tmp.name, self.xib_tmp.name])
            self.assertEqual(code, 0)
            with open(gen_tmp.name, "rb") as f:
                raw = f.read()
            text = raw.decode("utf-8", errors="replace")
            # 値は空 ("Hello World" ではなく "")
            if "title" in text:
                # title = ""; のような形式
                self.assertIn('" = ""', text)
        finally:
            if os.path.exists(gen_tmp.name):
                os.unlink(gen_tmp.name)


class TestStringsImport(unittest.TestCase):
    """--import-strings-file の検証"""

    def setUp(self):
        self.xib_tmp = tempfile.NamedTemporaryFile(suffix=".xib", delete=False, mode="w", encoding="utf-8")
        self.xib_tmp.write(XIB_WITH_STRINGS)
        self.xib_tmp.close()

    def tearDown(self):
        if os.path.exists(self.xib_tmp.name):
            os.unlink(self.xib_tmp.name)

    def test_import_strings(self):
        """export → import round-trip"""
        str_tmp = tempfile.NamedTemporaryFile(suffix=".strings", delete=False)
        str_tmp.close()
        out_xib = tempfile.NamedTemporaryFile(suffix=".xib", delete=False)
        out_xib.close()
        try:
            code, _ = _run(["--export-strings-file", str_tmp.name, self.xib_tmp.name])
            self.assertEqual(code, 0)
            code, _ = _run(["--import-strings-file", str_tmp.name,
                           "--write", out_xib.name, self.xib_tmp.name])
            self.assertEqual(code, 0)
            self.assertGreater(os.path.getsize(out_xib.name), 0)
        finally:
            for p in [str_tmp.name, out_xib.name]:
                if os.path.exists(p):
                    os.unlink(p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
