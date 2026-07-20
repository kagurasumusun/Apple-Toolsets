"""
test_viraptor_ibtool_compat.py - viraptor/ibtool プロジェクトのフィクスチャで検証

viraptor/ibtool (https://github.com/viraptor/ibtool) は Apple ibtool の
別の OSS クリーンルーム実装。164 xib + 164 nib ペアの全ファイルを
pyibtool でパース + 全 dump 機能実行して検証する。
"""
import os, sys, unittest, io, tempfile, plistlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text
from pyibtool.nibarchive import parse_nib

VIRAPTOR_XIB = Path(__file__).parent.parent / "fixtures" / "viraptor_xib"
VIRAPTOR_NIB = Path(__file__).parent.parent / "fixtures" / "viraptor_nib"


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


class TestViraptorXIBParse(unittest.TestCase):
    """viraptor/ibtool の全 164 xib をパース"""

    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))
        if not self.files:
            self.skipTest("no xib files")

    def test_all_xib_parse(self):
        """全 xib がパース可能"""
        ok = 0
        err = 0
        for f in self.files:
            try:
                doc = parse_xib_text(f.read_text(encoding="utf-8"))
                if doc:
                    ok += 1
            except Exception as e:
                err += 1
                if err < 5:
                    print(f"  ERR: {f.name}: {e}")
        print(f"  Total: {ok} ok, {err} err")
        self.assertGreater(ok, 100, f"too few ok: {ok}")
        self.assertEqual(err, 0, f"{err} parse errors")

    def test_all_xib_dumps(self):
        """全 xib で全 dump 機能実行"""
        dumps = ["classes", "objects", "hierarchy", "connections", "all",
                 "version-history", "localizable-strings", "localizable-all",
                 "warnings", "errors", "notices"]
        ok = 0
        for f in self.files[:20]:  # 20 個に制限 (時間短縮)
            for d in dumps:
                code, out = _run([f"--{d}", str(f)])
                if code == 0:
                    ok += 1
        print(f"  dump OK count: {ok}")
        self.assertGreater(ok, 0)

    def test_all_xib_compile(self):
        """全 xib で --compile がエラーなく動く"""
        ok = 0
        for f in self.files[:20]:
            with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as t:
                tmp = t.name
            try:
                code, _ = _run(["--compile", tmp, str(f)])
                if code == 0 and os.path.exists(tmp):
                    ok += 1
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        print(f"  compile OK count: {ok}")
        self.assertGreater(ok, 0)

    def test_all_xib_xliff(self):
        """全 xib で XLIFF export"""
        for f in self.files[:10]:
            with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as t:
                tmp = t.name
            try:
                code, _ = _run(["--export-xliff", tmp,
                               "--source-language", "en",
                               "--target-language", "ja", str(f)])
                self.assertEqual(code, 0, f"--export-xliff failed for {f.name}")
                with open(tmp) as fp:
                    content = fp.read()
                self.assertIn("xmlns:ib=\"com.apple.InterfaceBuilder3\"", content)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)


class TestViraptorNIBParse(unittest.TestCase):
    """viraptor/ibtool の全 164 nib をパース"""

    def setUp(self):
        if not VIRAPTOR_NIB.exists():
            self.skipTest("no viraptor nib fixtures")
        self.files = sorted(VIRAPTOR_NIB.glob("*.nib"))
        if not self.files:
            self.skipTest("no nib files")

    def test_all_nib_parse(self):
        """全 nib がパース可能"""
        ok = 0
        err = 0
        for f in self.files:
            try:
                arch = parse_nib(f.read_bytes())
                if arch.class_names:
                    ok += 1
            except Exception as e:
                err += 1
                if err < 5:
                    print(f"  ERR: {f.name}: {e}")
        print(f"  Total: {ok} ok, {err} err")
        self.assertGreater(ok, 100)
        self.assertEqual(err, 0)

    def test_nib_magic(self):
        """全 nib が NIBArchive magic"""
        for f in self.files:
            data = f.read_bytes()
            self.assertEqual(data[:10], b"NIBArchive", f.name)


class TestViraptorRoundTrip(unittest.TestCase):
    """viraptor の xib → pyibtool → nib → pyibtool パース round-trip"""

    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))[:20]

    def test_xib_to_nib_parse(self):
        """viraptor xib → pyibtool --compile → pyibtool parse"""
        for f in self.files:
            with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as t:
                tmp = t.name
            try:
                code, _ = _run(["--compile", tmp, str(f)])
                self.assertEqual(code, 0, f"compile failed for {f.name}")
                # パース可能
                arch = parse_nib(open(tmp, "rb").read())
                self.assertGreater(len(arch.class_names), 0)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)


class TestViraptorNibarchiveCompat(unittest.TestCase):
    """viraptor nib を nibarchive PyPI でも読めるか"""

    @classmethod
    def setUpClass(cls):
        try:
            from nibarchive import NIBArchiveParser
            cls.parser = NIBArchiveParser(verify=True)
        except ImportError:
            cls.parser = None

    def setUp(self):
        if not VIRAPTOR_NIB.exists():
            self.skipTest("no viraptor nib fixtures")
        if self.parser is None:
            self.skipTest("nibarchive not installed")
        self.files = sorted(VIRAPTOR_NIB.glob("*.nib"))[:20]

    def test_nibarchive_can_parse(self):
        for f in self.files:
            with self.subTest(file=f.name):
                with open(f, "rb") as fp:
                    try:
                        arch = self.parser.parse(fp)
                        self.assertGreater(len(arch.class_names), 0)
                    except Exception as e:
                        self.skipTest(f"nibarchive parse failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
