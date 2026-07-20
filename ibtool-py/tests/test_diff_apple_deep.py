"""
test_diff_apple_deep.py - Apple dump 出力と pyibtool 出力の deep diff

実機の Apple ibtool (Xcode 26.5) で取得した dump 系 plist と
pyibtool の出力を 1 対 1 で比較し、差分を報告する。
"""
import os, sys, plistlib, io, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool

FIXTURES = Path(__file__).parent.parent / "fixtures" / "probe_v8"


def _run(args, binary=False):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        sys.stdout = io.BytesIO() if binary else io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        return code, out
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestAppleDeepDiff(unittest.TestCase):
    """Apple dump 出力と pyibtool 出力の値レベルでの比較"""

    def setUp(self):
        self.xib = FIXTURES / "ios.xib"
        if not self.xib.exists():
            self.skipTest("no ios.xib fixture")

    def _get_dump(self, dump_name):
        apple_path = FIXTURES / f"ios_{dump_name}.plist"
        if not apple_path.exists():
            self.skipTest(f"no {apple_path.name}")
        apple = plistlib.loads(open(apple_path, "rb").read())
        code, out = _run([f"--{dump_name}", str(self.xib)])
        self.assertEqual(code, 0, f"pyibtool {dump_name} failed")
        pyib = plistlib.loads(out)
        return apple, pyib

    def test_all_keys_match(self):
        """--all のキー数が Apple と一致"""
        apple, pyib = self._get_dump("all")
        self.assertEqual(set(apple.keys()), set(pyib.keys()))

    def test_classes_match(self):
        """--classes: Apple 176 クラスと同じ数"""
        apple = list(apple["com.apple.ibtool.document.classes"].keys()
                     for apple in [self._get_dump("classes")[0]])[0]
        pyib = list(self._get_dump("classes")[1]["com.apple.ibtool.document.classes"].keys())
        self.assertEqual(set(apple), set(pyib),
                          f"classes differ: only Apple={set(apple) - set(pyib)}, only pyibtool={set(pyib) - set(apple)}")

    def test_hierarchy_match(self):
        """--hierarchy: 構造完全一致"""
        apple = self._get_dump("hierarchy")[0]["com.apple.ibtool.document.hierarchy"]
        pyib = self._get_dump("hierarchy")[1]["com.apple.ibtool.document.hierarchy"]
        self.assertEqual(apple, pyib)

    def test_version_history_match(self):
        """--version-history: Apple は dict 形式、pyibtool も同様"""
        apple = self._get_dump("version-history")[0]["com.apple.ibtool.document.version-history"]
        pyib = self._get_dump("version-history")[1]["com.apple.ibtool.document.version-history"]
        self.assertEqual(apple, pyib)

    def test_localizable_other_empty(self):
        """--localizable-other: Apple 出力は空 dict"""
        apple = self._get_dump("localizable-other")[0]["com.apple.ibtool.document.localizable-other"]
        pyib = self._get_dump("localizable-other")[1]["com.apple.ibtool.document.localizable-other"]
        self.assertEqual(apple, pyib)
        self.assertEqual(apple, {})

    def test_localizable_stringarrays_empty(self):
        """--localizable-stringarrays: 空 dict"""
        apple = self._get_dump("localizable-stringarrays")[0]["com.apple.ibtool.document.localizable-stringarrays"]
        pyib = self._get_dump("localizable-stringarrays")[1]["com.apple.ibtool.document.localizable-stringarrays"]
        self.assertEqual(apple, pyib)
        self.assertEqual(apple, {})

    def test_localizable_to_many_empty(self):
        """--localizable-to-many-relationships: 空 dict"""
        apple = self._get_dump("localizable-to-many-relationships")[0]["com.apple.ibtool.document.localizable-to-many-relationships"]
        pyib = self._get_dump("localizable-to-many-relationships")[1]["com.apple.ibtool.document.localizable-to-many-relationships"]
        self.assertEqual(apple, pyib)
        self.assertEqual(apple, {})

    def test_warnings_empty(self):
        """--warnings: 空 dict"""
        apple = self._get_dump("warnings")[0]["com.apple.ibtool.document.warnings"]
        pyib = self._get_dump("warnings")[1]["com.apple.ibtool.document.warnings"]
        self.assertEqual(apple, pyib)
        self.assertEqual(apple, {})

    def test_errors_empty(self):
        """--errors: 空 dict"""
        apple = self._get_dump("errors")[0]["com.apple.ibtool.document.errors"]
        pyib = self._get_dump("errors")[1]["com.apple.ibtool.document.errors"]
        self.assertEqual(apple, pyib)
        self.assertEqual(apple, {})

    def test_notices_empty(self):
        """--notices: 空 dict"""
        apple = self._get_dump("notices")[0]["com.apple.ibtool.document.notices"]
        pyib = self._get_dump("notices")[1]["com.apple.ibtool.document.notices"]
        self.assertEqual(apple, pyib)
        self.assertEqual(apple, {})

    def test_connections_empty(self):
        """--connections: 空 dict (no connections in this xib)"""
        apple = self._get_dump("connections")[0]["com.apple.ibtool.document.connections"]
        pyib = self._get_dump("connections")[1]["com.apple.ibtool.document.connections"]
        self.assertEqual(apple, pyib)

    def test_localizable_all_keys(self):
        """--localizable-all: 8 フィールド存在"""
        apple = self._get_dump("localizable-all")[0]["com.apple.ibtool.document.localizable-all"]
        pyib = self._get_dump("localizable-all")[1]["com.apple.ibtool.document.localizable-all"]
        # 同じ id (iN0-l3-epB) を持つこと
        self.assertEqual(set(apple.keys()), set(pyib.keys()))
        # 同じ key を持つこと
        a_first = list(apple.values())[0]
        p_first = list(pyib.values())[0]
        self.assertEqual(set(a_first.keys()), set(p_first.keys()))

    def test_localizable_all_values(self):
        """--localizable-all: 8 フィールドの値が一致"""
        apple = self._get_dump("localizable-all")[0]["com.apple.ibtool.document.localizable-all"]
        pyib = self._get_dump("localizable-all")[1]["com.apple.ibtool.document.localizable-all"]
        for oid in apple:
            self.assertIn(oid, pyib)
            for k, v in apple[oid].items():
                self.assertEqual(pyib[oid][k], v, f"{oid}.{k}: Apple={v!r} pyibtool={pyib[oid][k]!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
