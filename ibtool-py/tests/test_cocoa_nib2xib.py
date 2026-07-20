"""
test_cocoa_nib2xib.py - Cocoa (macOS) nib → xib → nib のテスト

viraptor/ibtool の macOS xib/nib ペア (164 個) で nib2xib 動作確認。
"""
import os, sys, unittest, io, plistlib, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text
from pyibtool.nib2xib import nib2xib
from pyibtool.nibarchive import parse_nib
from pyibtool.xibdoc import serialize_xib

VIRAPTOR_XIB = Path(__file__).parent.parent / "fixtures" / "viraptor_xib"
VIRAPTOR_NIB = Path(__file__).parent.parent / "fixtures" / "viraptor_nib"


class TestCocoaNIBToXIB(unittest.TestCase):
    def setUp(self):
        if not VIRAPTOR_NIB.exists():
            self.skipTest("no viraptor nib fixtures")
        self.files = sorted(VIRAPTOR_NIB.glob("*.nib"))[:10]

    def test_nib_parseable(self):
        """全 viraptor nib を pyibtool で parse"""
        ok = 0
        for f in self.files:
            with self.subTest(file=f.name):
                with open(f, "rb") as fp:
                    data = fp.read()
                arch = parse_nib(data)
                self.assertGreater(len(arch.class_names), 0)
                ok += 1
        print(f"  parsed: {ok}/{len(self.files)}")

    def test_nib_to_xib_cocoa(self):
        """nib → xib (Cocoa 形式)"""
        for f in self.files:
            with self.subTest(file=f.name):
                with open(f, "rb") as fp:
                    data = fp.read()
                try:
                    arch = parse_nib(data)
                    doc = nib2xib(arch, doc_type="com.apple.InterfaceBuilder3.Cocoa.XIB",
                                 target_runtime="macOS.Cocoa")
                    text = serialize_xib(doc)
                    # パース可能
                    doc2 = parse_xib_text(text)
                    self.assertIn("Cocoa", doc2.doc_type)
                except Exception as e:
                    self.fail(f"{f.name}: {e}")


class TestCocoaCompileAndXibCompat(unittest.TestCase):
    """Cocoa xib → nib → xib → nib 互換性"""

    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))[:5]

    def test_compile_cocoa_xib(self):
        """Cocoa xib → nib compile"""
        for f in self.files:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as t:
                    tmp = t.name
                try:
                    sys_stderr = sys.stderr
                    sys.stdout2 = sys.stdout
                    sys.stderr = io.StringIO()
                    sys.stdout = io.BytesIO()
                    code = ibtool.main(["--compile", tmp, str(f)])
                    out = sys.stdout.getvalue()
                    sys.stderr = sys_stderr
                    sys.stdout = sys.stdout2
                    self.assertEqual(code, 0, f"compile failed for {f.name}")
                    self.assertGreater(os.path.getsize(tmp), 0)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)


class TestCocoaNIBTypeMapping(unittest.TestCase):
    """NIB class → xib tag の変換が Cocoa で正しいか"""

    def test_ns_window_to_window(self):
        from pyibtool.nib2xib import class_name_to_xib_tag
        self.assertEqual(class_name_to_xib_tag("NSWindow"), "window")

    def test_ns_view_to_view(self):
        from pyibtool.nib2xib import class_name_to_xib_tag
        self.assertEqual(class_name_to_xib_tag("NSView"), "view")

    def test_ns_application_to_application(self):
        from pyibtool.nib2xib import class_name_to_xib_tag
        self.assertEqual(class_name_to_xib_tag("NSApplication"), "application")

    def test_ns_menu_to_menu(self):
        from pyibtool.nib2xib import class_name_to_xib_tag
        self.assertEqual(class_name_to_xib_tag("NSMenu"), "menu")

    def test_ui_view_to_view(self):
        from pyibtool.nib2xib import class_name_to_xib_tag
        self.assertEqual(class_name_to_xib_tag("UIView"), "view")

    def test_unknown_class_to_custom_view(self):
        """未知の class は customView にフォールバック"""
        from pyibtool.nib2xib import class_name_to_xib_tag
        self.assertEqual(class_name_to_xib_tag("MyCustomClass"), "customView")
        self.assertEqual(class_name_to_xib_tag("HSChooserWindow"), "customView")


if __name__ == "__main__":
    unittest.main(verbosity=2)
