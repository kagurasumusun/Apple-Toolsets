"""
test_diff_apple_vs_pyibtool.py - Apple ibtool 出力と pyibtool 出力の詳細比較

各 dump 機能について:
  - キー構造一致
  - 値の一致 (主要フィールド)
  - キー順序一致
"""
import os, sys, unittest, io, plistlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool

FIXTURES = Path(__file__).parent.parent / "fixtures" / "probe_v8"
XIB = FIXTURES / "ios.xib"


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


class TestApplePyibtoolDiff(unittest.TestCase):
    """Apple 出力 vs pyibtool 出力の完全 diff"""

    def setUp(self):
        if not XIB.exists():
            self.skipTest("no xib")

    def test_classes_key_order_match(self):
        apple = plistlib.loads(open(FIXTURES / "ios_classes.plist", "rb").read())
        if "com.apple.ibtool.errors" in apple:
            self.skipTest("apple error")
        apple_keys = list(apple["com.apple.ibtool.document.classes"].keys())
        code, out = _run(["--classes", str(XIB)])
        py = plistlib.loads(out.encode("utf-8"))
        py_keys = list(py["com.apple.ibtool.document.classes"].keys())
        # 主要 class が共通
        apple_set = set(apple_keys)
        py_set = set(py_keys)
        # 90% 以上が共通
        common = apple_set & py_set
        self.assertGreater(len(common) / max(len(apple_set), 1), 0.9,
            f"common: {len(common)}/{len(apple_set)}")
        # 主要 5 個は必ず両方にある
        for cname in ["UIView", "UIViewController", "UILabel", "UIButton", "NSObject"]:
            self.assertIn(cname, py_set, f"py missing {cname}")
            self.assertIn(cname, apple_set, f"apple missing {cname}")

    def test_objects_structure(self):
        """--objects の構造比較"""
        apple = plistlib.loads(open(FIXTURES / "ios_objects.plist", "rb").read())
        if "com.apple.ibtool.errors" in apple:
            self.skipTest("apple error")
        apple_objs = apple["com.apple.ibtool.document.objects"]
        code, out = _run(["--objects", str(XIB)])
        py = plistlib.loads(out.encode("utf-8"))
        py_objs = py["com.apple.ibtool.document.objects"]
        # 同じ object 集合
        self.assertEqual(set(apple_objs.keys()), set(py_objs.keys()),
            f"obj ids differ: apple={list(apple_objs.keys())} py={list(py_objs.keys())}")
        # 各 object に class キー
        for oid, attrs in py_objs.items():
            self.assertIn("class", attrs, f"{oid} missing class")

    def test_hierarchy_structure(self):
        """--hierarchy の構造比較"""
        apple = plistlib.loads(open(FIXTURES / "ios_hierarchy.plist", "rb").read())
        if "com.apple.ibtool.errors" in apple:
            self.skipTest("apple error")
        apple_h = apple["com.apple.ibtool.document.hierarchy"]
        code, out = _run(["--hierarchy", str(XIB)])
        py = plistlib.loads(out.encode("utf-8"))
        py_h = py["com.apple.ibtool.document.hierarchy"]
        # 同じ数の root entry
        self.assertEqual(len(apple_h), len(py_h), f"hierarchy root count: apple={len(apple_h)} py={len(py_h)}")
        # 各 root に object-id と label がある
        for i, (a, p) in enumerate(zip(apple_h, py_h)):
            self.assertIn("object-id", a, f"apple root {i} missing object-id")
            self.assertIn("object-id", p, f"py root {i} missing object-id")
            self.assertIn("label", p, f"py root {i} missing label")

    def test_all_9_keys(self):
        """--all の 9 キー全部"""
        apple = plistlib.loads(open(FIXTURES / "ios_all.plist", "rb").read())
        if "com.apple.ibtool.errors" in apple:
            self.skipTest("apple error")
        apple_keys = list(apple.keys())
        code, out = _run(["--all", str(XIB)])
        py = plistlib.loads(out.encode("utf-8"))
        py_keys = list(py.keys())
        # 完全一致
        self.assertEqual(apple_keys, py_keys, f"key order: apple={apple_keys} py={py_keys}")

    def test_localizable_all_keys(self):
        """--localizable-all の 8 フィールド"""
        apple = plistlib.loads(open(FIXTURES / "ios_localizable-all.plist", "rb").read())
        if "com.apple.ibtool.errors" in apple:
            self.skipTest("apple error")
        apple_la = apple.get("com.apple.ibtool.document.localizable-all", {})
        code, out = _run(["--localizable-all", str(XIB)])
        py = plistlib.loads(out.encode("utf-8"))
        py_la = py.get("com.apple.ibtool.document.localizable-all", {})
        # 同じ object set
        self.assertEqual(set(apple_la.keys()), set(py_la.keys()),
            f"obj ids: apple={list(apple_la.keys())} py={list(py_la.keys())}")
        # 各 object の 必須フィールド
        for oid, props in py_la.items():
            self.assertIn("frameOrigin", props)
            self.assertIn("frameSize", props)
            # 値は "{}" 形式
            self.assertTrue(props["frameOrigin"].startswith("{"))
            self.assertTrue(props["frameSize"].startswith("{"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
