"""
test_macos_xib_dump.py - macOS Cocoa xib で全 dump 機能動作確認

viraptor/ibtool プロジェクトの macOS xib (164 個) で pyibtool の全 dump 系を実行
"""
import os, sys, unittest, io, plistlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool

VIRAPTOR_XIB = Path(__file__).parent.parent / "fixtures" / "viraptor_xib"


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


class TestCocoaXDump(unittest.TestCase):
    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))[:20]

    def test_classes_dump(self):
        for f in self.files:
            with self.subTest(file=f.name):
                code, out = _run(["--classes", str(f)])
                self.assertEqual(code, 0)
                d = plistlib.loads(out.encode("utf-8"))
                self.assertIn("com.apple.ibtool.document.classes", d)

    def test_objects_dump(self):
        for f in self.files:
            with self.subTest(file=f.name):
                code, out = _run(["--objects", str(f)])
                self.assertEqual(code, 0)
                d = plistlib.loads(out.encode("utf-8"))
                self.assertIn("com.apple.ibtool.document.objects", d)

    def test_hierarchy_dump(self):
        for f in self.files:
            with self.subTest(file=f.name):
                code, out = _run(["--hierarchy", str(f)])
                self.assertEqual(code, 0)
                d = plistlib.loads(out.encode("utf-8"))
                self.assertIn("com.apple.ibtool.document.hierarchy", d)

    def test_connections_dump(self):
        for f in self.files:
            with self.subTest(file=f.name):
                code, out = _run(["--connections", str(f)])
                self.assertEqual(code, 0)
                d = plistlib.loads(out.encode("utf-8"))
                self.assertIn("com.apple.ibtool.document.connections", d)

    def test_all_dump(self):
        for f in self.files:
            with self.subTest(file=f.name):
                code, out = _run(["--all", str(f)])
                self.assertEqual(code, 0)
                d = plistlib.loads(out.encode("utf-8"))
                # 9 キー全部
                expected = [
                    "com.apple.ibtool.document.classes",
                    "com.apple.ibtool.document.connections",
                    "com.apple.ibtool.document.errors",
                    "com.apple.ibtool.document.hierarchy",
                    "com.apple.ibtool.document.localizable-all",
                    "com.apple.ibtool.document.notices",
                    "com.apple.ibtool.document.objects",
                    "com.apple.ibtool.document.version-history",
                    "com.apple.ibtool.document.warnings",
                ]
                for k in expected:
                    self.assertIn(k, d, f"missing {k} in {f.name}")


class TestCocoaXCompile(unittest.TestCase):
    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))[:20]

    def test_compile(self):
        import tempfile
        for f in self.files:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as t:
                    tmp = t.name
                try:
                    code, _ = _run(["--compile", tmp, str(f)])
                    self.assertEqual(code, 0, f"compile failed for {f.name}")
                    self.assertGreater(os.path.getsize(tmp), 0)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)


class TestCocoaXXliff(unittest.TestCase):
    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))[:10]

    def test_xliff_export(self):
        import tempfile
        for f in self.files:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as t:
                    tmp = t.name
                try:
                    code, _ = _run(["--export-xliff", tmp,
                                   "--source-language", "en",
                                   "--target-language", "ja", str(f)])
                    self.assertEqual(code, 0)
                    with open(tmp) as fp:
                        content = fp.read()
                    self.assertIn("xmlns:ib=\"com.apple.InterfaceBuilder3\"", content)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
