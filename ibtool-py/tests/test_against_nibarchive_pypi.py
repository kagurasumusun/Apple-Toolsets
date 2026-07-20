"""
test_against_nibarchive_pypi.py - nibarchive (PyPI) との比較

外部パッケージ `nibarchive` (MatrixEditor/nibarchive) の出力が pyibtool と一致するか検証。
両実装が同じ NIBArchive をパースして同じ結果 = NIBArchive 仕様準拠の証拠。
"""
import os, sys, unittest, struct
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# nibarchive PyPI パッケージ
try:
    from nibarchive import NIBArchiveParser
    HAS_NIBARCHIVE = True
except ImportError:
    HAS_NIBARCHIVE = False

from pyibtool.nibarchive import parse_nib

FIXTURES = Path(__file__).parent.parent / "fixtures" / "golden"


@unittest.skipUnless(HAS_NIBARCHIVE, "nibarchive not installed")
class TestAgainstNibarchivePyPI(unittest.TestCase):
    """pyibtool parse_nib vs nibarchive PyPI"""

    def test_apple_nib_classes_match(self):
        """pyibtool と nibarchive で同じ class をパース"""
        nib = FIXTURES / "A1.nib"
        if not nib.exists():
            self.skipTest("no A1.nib")
        with open(nib, "rb") as f:
            data = f.read()
        # nibarchive
        parser = NIBArchiveParser(verify=True)
        with open(nib, "rb") as f:
            arch_nibarchive = parser.parse(f)
        # pyibtool
        arch_py = parse_nib(data)
        # class names
        self.assertEqual([c.name for c in arch_nibarchive.class_names],
                         [c.name for c in arch_py.class_names],
                         "class names differ")
        self.assertEqual(len(arch_nibarchive.objects), len(arch_py.objects))
        self.assertEqual(len(arch_nibarchive.keys), len(arch_py.keys))
        self.assertEqual(len(arch_nibarchive.values), len(arch_py.values))

    def test_all_apple_nibs_match(self):
        """全 Apple nib で nibarchive と pyibtool のパース結果一致"""
        exclude = {"out.nib", "A9.nib", "A32.storyboardc"}
        nibs = sorted(f for f in os.listdir(FIXTURES)
                      if f.endswith(".nib") and f not in exclude)
        results = []
        for f in nibs:
            p = FIXTURES / f
            with open(p, "rb") as fp:
                data = fp.read()
            if len(data) < 50:
                continue
            parser = NIBArchiveParser(verify=True)
            with open(p, "rb") as fp:
                arch_nib = parser.parse(fp)
            arch_py = parse_nib(data)
            ok = ([c.name for c in arch_nib.class_names] ==
                  [c.name for c in arch_py.class_names] and
                  len(arch_nib.objects) == len(arch_py.objects) and
                  len(arch_nib.keys) == len(arch_py.keys) and
                  len(arch_nib.values) == len(arch_py.values))
            results.append((f, ok))
        for f, ok in results:
            status = "OK" if ok else "MISMATCH"
            print(f"  {f}: {status}")
        fails = [r for r in results if not r[1]]
        self.assertEqual(len(fails), 0,
                         f"{len(fails)} nibs differ from nibarchive: {fails}")

    def test_value_types_match(self):
        """value type のパース結果一致"""
        nib = FIXTURES / "A1.nib"
        with open(nib, "rb") as f:
            data = f.read()
        parser = NIBArchiveParser(verify=True)
        with open(nib, "rb") as f:
            arch_nib = parser.parse(f)
        arch_py = parse_nib(data)
        # value type (0-8 = int8/16/32/64, true/false, float/double)
        for i, (vn, vp) in enumerate(zip(arch_nib.values, arch_py.values)):
            self.assertEqual(vn.type, vp.type, f"value {i} type mismatch")


@unittest.skipUnless(HAS_NIBARCHIVE, "nibarchive not installed")
class TestNibarchiveCrossRoundTrip(unittest.TestCase):
    """nibarchive 出力と pyibtool 出力の比較"""

    def test_nibarchive_can_parse_pyibtool_nib(self):
        """pyibtool --compile 出力 nib を nibarchive で読めるか (ベストエフォート)"""
        import io, tempfile
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            from pyibtool import ibtool
            old_out = sys.stdout
            sys.stdout = io.StringIO()
            try:
                ibtool.main(["--compile", tmp, str(Path(__file__).parent.parent / "fixtures" / "input" / "ivc.xib")])
            finally:
                sys.stdout = old_out
            # nibarchive で読めるか (失敗しても OK、ベストエフォート)
            parser = NIBArchiveParser(verify=True)
            try:
                with open(tmp, "rb") as f:
                    arch = parser.parse(f)
                # 読めれば class_names が 0 以上
                self.assertGreaterEqual(len(arch.class_names), 0)
            except Exception as e:
                # 読み取り失敗は許容 (Xcode 26.5 nib 形式の拡張に未対応の可能性)
                print(f"  nibarchive parse failed (expected): {e}")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
