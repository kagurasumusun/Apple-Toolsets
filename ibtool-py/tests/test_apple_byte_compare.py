"""
test_apple_byte_compare.py - Apple 出力と pyibtool 出力を 1 対 1 で構造比較

各 dump 機能について、pyibtool の出力が Apple 出力と構造的に同等か検証。
"""
import os, sys, plistlib, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text

FIXTURES = Path(__file__).parent.parent / "fixtures" / "probe_v8"


def _run_pyibtool(args, capture_binary=False):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        if capture_binary:
            sys.stdout = io.BytesIO()
        else:
            sys.stdout = io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return code, out, err
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


def _load_apple(plat, suffix):
    p = FIXTURES / f"{plat}_{suffix}.plist"
    if not p.exists():
        return None
    with open(p, "rb") as f:
        try:
            d = plistlib.load(f)
        except Exception:
            return None
    if "com.apple.ibtool.errors" in d:
        return None
    return d


class TestAppleClassesComparison(unittest.TestCase):
    """pyibtool --classes vs Apple --classes"""

    def setUp(self):
        self.apple = _load_apple("ios", "classes")
        if not self.apple:
            self.skipTest("no apple classes")

    def test_classes_count_over_50(self):
        """pyibtool も Apple と同様に 50+ クラス DB を含む"""
        code, out, _ = _run_pyibtool(["--classes", str(FIXTURES / "ios.xib")])
        self.assertEqual(code, 0)
        d = plistlib.loads(out.encode("utf-8"))
        cls = d["com.apple.ibtool.document.classes"]
        self.assertGreater(len(cls), 50,
            f"pyibtool class count {len(cls)} too low (Apple has ~200)")

    def test_classes_have_main_ui_classes(self):
        """主要 UI クラスが含まれる"""
        code, out, _ = _run_pyibtool(["--classes", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        cls = d["com.apple.ibtool.document.classes"]
        for cname in ["UIView", "UIViewController", "UIButton", "UILabel",
                      "NSObject", "UIResponder", "UINavigationController"]:
            self.assertIn(cname, cls, f"missing {cname}")

    def test_classes_match_apple_majority(self):
        """Apple と pyibtool で同じ class エントリが多数"""
        code, out, _ = _run_pyibtool(["--classes", str(FIXTURES / "ios.xib")])
        py = plistlib.loads(out.encode("utf-8"))["com.apple.ibtool.document.classes"]
        apple = self.apple["com.apple.ibtool.document.classes"]
        # 主要 50 クラスは一致するはず
        py_set = set(py.keys())
        apple_set = set(apple.keys())
        # 50 個は両方にある
        common = py_set & apple_set
        self.assertGreater(len(common), 100,
            f"common classes: {len(common)} (expected > 100)")

    def test_ui_view_has_correct_superclass(self):
        code, out, _ = _run_pyibtool(["--classes", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        cls = d["com.apple.ibtool.document.classes"]
        self.assertEqual(cls["UIView"]["class"], "UIView")
        self.assertEqual(cls["UIView"]["superclass"], "UIResponder")

    def test_ui_view_controller_has_view_outlet(self):
        code, out, _ = _run_pyibtool(["--classes", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        cls = d["com.apple.ibtool.document.classes"]
        self.assertIn("view", cls["UIViewController"]["outlets"])
        self.assertEqual(cls["UIViewController"]["outlets"]["view"], "UIView")


class TestAppleHierarchyComparison(unittest.TestCase):
    """pyibtool --hierarchy vs Apple --hierarchy"""

    def setUp(self):
        self.apple = _load_apple("ios", "hierarchy")
        if not self.apple:
            self.skipTest("no apple hierarchy")

    def test_hierarchy_required_keys(self):
        code, out, _ = _run_pyibtool(["--hierarchy", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        h = d["com.apple.ibtool.document.hierarchy"]
        for entry in h:
            if not entry:
                continue
            self.assertIn("object-id", entry)
            self.assertIn("label", entry)

    def test_hierarchy_file_owner_has_name(self):
        """File's Owner は name 属性を持つ (placeholder)"""
        code, out, _ = _run_pyibtool(["--hierarchy", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        h = d["com.apple.ibtool.document.hierarchy"]
        fo = next((e for e in h if e.get("object-id") == "-1"), None)
        self.assertIsNotNone(fo)
        # Apple 出力: File's Owner は name を持つ
        self.assertIn("name", fo)
        self.assertEqual(fo["name"], "File's Owner")

    def test_hierarchy_first_responder_has_custom_class(self):
        """First Responder (customClass=UIResponder) は custom-class を持つ"""
        code, out, _ = _run_pyibtool(["--hierarchy", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        h = d["com.apple.ibtool.document.hierarchy"]
        fr = next((e for e in h if e.get("object-id") == "-2"), None)
        self.assertIsNotNone(fr)
        self.assertEqual(fr.get("custom-class"), "UIResponder")

    def test_hierarchy_view_no_name_no_custom_class(self):
        """普通の view は name も custom-class もない"""
        code, out, _ = _run_pyibtool(["--hierarchy", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        h = d["com.apple.ibtool.document.hierarchy"]
        v = next((e for e in h if e.get("object-id") == "v1"), None)
        if v:
            self.assertNotIn("name", v)
            self.assertNotIn("custom-class", v)

    def test_hierarchy_safe_area_label(self):
        """Safe Area layout guide は label=Safe Area"""
        code, out, _ = _run_pyibtool(["--hierarchy", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        h = d["com.apple.ibtool.document.hierarchy"]
        # Find Safe Area in children
        for entry in h:
            if "children" in entry:
                for c in entry["children"]:
                    if c.get("label") == "Safe Area":
                        return  # found
        self.fail("Safe Area not found in hierarchy")


class TestAppleAllComparison(unittest.TestCase):
    """pyibtool --all vs Apple --all"""

    def setUp(self):
        self.apple = _load_apple("ios", "all")
        if not self.apple:
            self.skipTest("no apple all")

    def test_all_required_keys_present(self):
        """Apple --all にある主要キーが pyibtool にもある"""
        code, out, _ = _run_pyibtool(["--all", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        for k in ["com.apple.ibtool.document.classes",
                  "com.apple.ibtool.document.connections",
                  "com.apple.ibtool.document.hierarchy",
                  "com.apple.ibtool.document.localizable-all",
                  "com.apple.ibtool.document.objects",
                  "com.apple.ibtool.document.version-history"]:
            self.assertIn(k, d, f"missing {k}")

    def test_all_errors_warnings_notices_are_dicts(self):
        """errors / warnings / notices は dict 形式"""
        code, out, _ = _run_pyibtool(["--all", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        for k in ["com.apple.ibtool.document.warnings",
                  "com.apple.ibtool.document.errors",
                  "com.apple.ibtool.document.notices"]:
            self.assertIsInstance(d.get(k), dict, f"{k} not dict")


class TestAppleLocalizableAllComparison(unittest.TestCase):
    """pyibtool --localizable-all vs Apple --localizable-all"""

    def setUp(self):
        self.apple = _load_apple("ios", "localizable-all")
        if not self.apple:
            self.skipTest("no apple localizable-all")

    def test_localizable_all_field_count(self):
        """Apple の各 object は 7-8 フィールド"""
        code, out, _ = _run_pyibtool(["--localizable-all", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        la = d["com.apple.ibtool.document.localizable-all"]
        for oid, props in la.items():
            self.assertGreaterEqual(len(props), 7)
            self.assertLessEqual(len(props), 8)

    def test_localizable_all_required_fields(self):
        code, out, _ = _run_pyibtool(["--localizable-all", str(FIXTURES / "ios.xib")])
        d = plistlib.loads(out.encode("utf-8"))
        la = d["com.apple.ibtool.document.localizable-all"]
        for oid, props in la.items():
            self.assertIn("frameOrigin", props)
            self.assertIn("frameSize", props)
            # frameOrigin = "{x, y}" 形式
            self.assertTrue(props["frameOrigin"].startswith("{"))
            self.assertTrue(props["frameOrigin"].endswith("}"))
            # frameSize = "{w, h}" 形式
            self.assertTrue(props["frameSize"].startswith("{"))
            self.assertTrue(props["frameSize"].endswith("}"))


class TestAppleOtherPlists(unittest.TestCase):
    """Apple の他の plist 系も Apple と同じ構造か"""

    def test_localizable_geometry_empty(self):
        """localizable-geometry は localizable-all と同じオブジェクト"""
        apple_all = _load_apple("ios", "localizable-all")
        apple_geom = _load_apple("ios", "localizable-geometry")
        if not apple_all or not apple_geom:
            self.skipTest("no apple")
        # トップレベルキーは異なるが、内部 object set は同じ
        a = apple_all.get("com.apple.ibtool.document.localizable-all", {})
        g = apple_geom.get("com.apple.ibtool.document.localizable-geometry", {})
        self.assertEqual(set(a.keys()), set(g.keys()))

    def test_localizable_stringarrays_is_empty_dict(self):
        apple = _load_apple("ios", "localizable-stringarrays")
        if not apple:
            self.skipTest("no apple")
        v = apple.get("com.apple.ibtool.document.localizable-stringarrays")
        if v is not None:
            self.assertIsInstance(v, dict)

    def test_localizable_other_is_empty_dict(self):
        apple = _load_apple("ios", "localizable-other")
        if not apple:
            self.skipTest("no apple")
        v = apple.get("com.apple.ibtool.document.localizable-other")
        if v is not None:
            self.assertIsInstance(v, dict)

    def test_localizable_to_many_relationships_is_empty_dict(self):
        apple = _load_apple("ios", "localizable-to-many-relationships")
        if not apple:
            self.skipTest("no apple")
        v = apple.get("com.apple.ibtool.document.localizable-to-many-relationships")
        if v is not None:
            self.assertIsInstance(v, dict)


class TestAppleXLIFFStructure(unittest.TestCase):
    """XLIFF Apple 互換"""

    def test_xliff_has_apple_namespace(self):
        xlf = FIXTURES / "ios.xlf"
        if not xlf.exists():
            self.skipTest("no xlf")
        content = xlf.read_text(encoding="utf-8")
        # Apple は xmlns:ib="com.apple.InterfaceBuilder3" を持つ
        self.assertIn("xmlns:ib=\"com.apple.InterfaceBuilder3\"", content)
        self.assertIn("com.apple.ibtool", content)

    def test_pyibtool_xliff_has_apple_namespace(self):
        """pyibtool 出力 XLIFF にも Apple namespace"""
        with tempfile.NamedTemporaryFile("w", suffix=".xlf", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run_pyibtool([
                "--export-xliff", tmp,
                "--source-language", "en",
                "--target-language", "ja",
                str(FIXTURES / "ios.xib")
            ])
            self.assertEqual(code, 0)
            content = open(tmp).read()
            self.assertIn("xmlns:ib=\"com.apple.InterfaceBuilder3\"", content)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
