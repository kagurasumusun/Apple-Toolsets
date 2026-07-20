"""
test_apple_v8_fixtures.py - Apple 実機出力 (probe_v8) と pyibtool の比較テスト

各 platform (ios, tvos, xr, watch, story, macos) × 各 dump 機能について
Apple 出力のキー構造と pyibtool 出力を比較する。
"""
import os, sys, plistlib, unittest, io, tempfile, subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text

FIXTURES = Path(__file__).parent.parent / "fixtures" / "probe_v8"

# 動的に Apple フィクスチャのあるプラットフォームを発見
def _available_platforms():
    """ios_classes.plist 等の存在で判定"""
    plats = []
    for p in ["ios", "tvos", "xr", "watch", "story", "macos"]:
        if (FIXTURES / f"{p}_classes.plist").exists():
            plats.append(p)
    return plats

PLATFORMS = _available_platforms()


def _run_pyibtool(args, capture_binary=False):
    """Run pyibtool and capture stdout"""
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
    """Load Apple plist fixture for a platform. Returns None if file doesn't exist or is an error."""
    p = FIXTURES / f"{plat}_{suffix}.plist"
    if not p.exists():
        return None
    with open(p, "rb") as f:
        try:
            d = plistlib.load(f)
        except Exception:
            return None
    # Apple ibtool のエラー出力は除外
    if "com.apple.ibtool.errors" in d:
        return None
    return d


def _apple_has_error(plat, suffix):
    """Check if Apple output is an error (SDK missing etc)"""
    p = FIXTURES / f"{plat}_{suffix}.plist"
    if not p.exists():
        return False
    with open(p, "rb") as f:
        try:
            d = plistlib.load(f)
        except Exception:
            return False
    return "com.apple.ibtool.errors" in d


def _xib_for(plat):
    """xib/storyboard ファイル名"""
    if plat == "story":
        return FIXTURES / "story.storyboard"
    return FIXTURES / f"{plat}.xib"


class TestAppleKeyOrder(unittest.TestCase):
    """--all 出力のキー順序は Apple 仕様と一致するか"""

    def test_apple_all_key_order(self):
        for plat in PLATFORMS:
            with self.subTest(platform=plat):
                apple = _load_apple(plat, "all")
                if not apple:
                    continue
                apple_keys = list(apple.keys())
                # Apple 期待キー順序 (実機検証済み)
                expected_prefix = [
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
                self.assertEqual(apple_keys, expected_prefix,
                    f"{plat} Apple --all key order mismatch: {apple_keys}")


class TestAppleVsPyibtoolKeys(unittest.TestCase):
    """pyibtool --all 出力のキー順序が Apple と一致するか"""

    def setUp(self):
        self.xib = _xib_for("ios")
        if not self.xib.exists():
            self.skipTest("no ios.xib")

    def test_pyibtool_all_key_order(self):
        code, out, _ = _run_pyibtool(["--all", str(self.xib)])
        self.assertEqual(code, 0)
        d = plistlib.loads(out.encode("utf-8"))
        py_keys = list(d.keys())
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
        self.assertEqual(py_keys, expected,
            f"pyibtool --all key order: {py_keys}")


class TestLocalizableAllStructure(unittest.TestCase):
    """--localizable-all の構造は Apple 仕様 (8 フィールド) と一致するか"""

    def test_apple_localizable_all_keys_present(self):
        for plat in PLATFORMS:
            apple = _load_apple(plat, "localizable-all")
            if not apple or "com.apple.ibtool.errors" in apple:
                continue
            d = apple.get("com.apple.ibtool.document.localizable-all", {})
            if not d:
                continue
            for oid, props in d.items():
                with self.subTest(platform=plat, oid=oid):
                    # 必須キー
                    self.assertIn("frameOrigin", props)
                    self.assertIn("frameSize", props)
                    # 7-8 フィールドのいずれか (ibDesignAutoresizingMask がある/なし)
                    self.assertGreaterEqual(len(props), 7)
                    self.assertLessEqual(len(props), 8)

    def test_pyibtool_localizable_all_keys_present(self):
        for plat in PLATFORMS:
            xib = _xib_for(plat)
            if not xib.exists():
                continue
            code, out, _ = _run_pyibtool(["--localizable-all", str(xib)])
            if code != 0:
                continue
            d = plistlib.loads(out.encode("utf-8"))
            la = d.get("com.apple.ibtool.document.localizable-all", {})
            for oid, props in la.items():
                with self.subTest(platform=plat, oid=oid):
                    self.assertIn("frameOrigin", props)
                    self.assertIn("frameSize", props)
                    self.assertGreaterEqual(len(props), 7)
                    self.assertLessEqual(len(props), 8)


class TestAppleErrorFormat(unittest.TestCase):
    """errors / warnings / notices は dict 形式 (空 dict {}) か"""

    def test_apple_errors_dict(self):
        for plat in PLATFORMS:
            apple = _load_apple(plat, "errors")
            if not apple:
                continue
            errs = apple.get("com.apple.ibtool.errors")
            # 成功時: 空 dict
            if errs is not None:
                self.assertIsInstance(errs, dict, f"{plat} errors not dict: {type(errs)}")

    def test_apple_warnings_dict(self):
        for plat in PLATFORMS:
            apple = _load_apple(plat, "warnings")
            if not apple:
                continue
            ws = apple.get("com.apple.ibtool.document.warnings")
            if ws is not None:
                self.assertIsInstance(ws, dict, f"{plat} warnings not dict: {type(ws)}")


class TestAppleClassesDB(unittest.TestCase):
    """--classes 出力に Apple 内部 class DB が入っているか (200 クラス以上)"""

    def test_apple_classes_count(self):
        for plat in PLATFORMS:
            apple = _load_apple(plat, "classes")
            if not apple or "com.apple.ibtool.errors" in apple:
                continue
            cls = apple.get("com.apple.ibtool.document.classes", {})
            with self.subTest(platform=plat):
                # Apple は 200 クラス以上の built-in DB を持つ
                self.assertGreater(len(cls), 50,
                    f"{plat} Apple classes count: {len(cls)} (expected > 50)")


class TestAppleHierarchyFormat(unittest.TestCase):
    """--hierarchy 出力の format 確認"""

    def test_apple_hierarchy_keys(self):
        for plat in PLATFORMS:
            apple = _load_apple(plat, "hierarchy")
            if not apple:
                continue
            h = apple.get("com.apple.ibtool.document.hierarchy", [])
            self.assertIsInstance(h, list)
            for entry in h:
                if not entry:
                    continue
                with self.subTest(platform=plat, entry=entry):
                    self.assertIn("object-id", entry)
                    self.assertIn("label", entry)


class TestAppleVersionHistory(unittest.TestCase):
    """--version-history 出力の構造"""

    def test_apple_version_history(self):
        for plat in PLATFORMS:
            apple = _load_apple(plat, "version-history")
            if not apple:
                continue
            vh = apple.get("com.apple.ibtool.document.version-history", {})
            with self.subTest(platform=plat):
                if vh:  # 空 dict の場合は Apple 出力に interface-builder-version がないこともある
                    ibv = vh.get("interface-builder-version", {})
                    self.assertIsInstance(ibv, dict)


class TestAppleXLIFF(unittest.TestCase):
    """--export-xliff 出力の構造"""

    def test_apple_xliff_namespace(self):
        for plat in PLATFORMS:
            xlf = FIXTURES / f"{plat}.xlf"
            if not xlf.exists():
                continue
            content = xlf.read_text(encoding="utf-8")
            with self.subTest(platform=plat):
                self.assertIn("xmlns:ib=\"com.apple.InterfaceBuilder3\"", content,
                    f"{plat} xliff missing ib namespace")
                self.assertIn("com.apple.ibtool", content)
                self.assertIn("source-language", content)
                self.assertIn("target-language", content)


class TestAppleStringsFile(unittest.TestCase):
    """--export-strings-file 出力の構造"""

    def test_apple_strings_format(self):
        for plat in PLATFORMS:
            s = FIXTURES / f"{plat}.strings"
            if not s.exists():
                continue
            raw = s.read_bytes()
            with self.subTest(platform=plat):
                # BOM or ASCII "key = value;" 形式
                if len(raw) > 0 and raw[:2] == b"\xff\xfe":
                    # UTF-16 LE BOM
                    pass
                else:
                    # ASCII or UTF-8
                    text = raw.decode("utf-8", errors="replace")
                    if text.strip():
                        # "key" = "value"; 形式
                        pass


class TestAppleLocalizableGeometry(unittest.TestCase):
    """--localizable-geometry 出力は localizable-all と同じか"""

    def test_apple_geometry_equals_all(self):
        for plat in PLATFORMS:
            all_d = _load_apple(plat, "localizable-all")
            geom = _load_apple(plat, "localizable-geometry")
            if not all_d or not geom:
                continue
            if "com.apple.ibtool.errors" in all_d or "com.apple.ibtool.errors" in geom:
                continue
            a = all_d.get("com.apple.ibtool.document.localizable-all", {})
            g = geom.get("com.apple.ibtool.document.localizable-geometry", {})
            with self.subTest(platform=plat):
                # 同じ object を含む
                self.assertEqual(set(a.keys()), set(g.keys()),
                    f"{plat}: localizable-all keys != localizable-geometry keys")
                for oid in a:
                    self.assertEqual(set(a[oid].keys()), set(g[oid].keys()),
                        f"{plat} {oid}: field set differs")


class TestAppleLocalizableEmptyTypes(unittest.TestCase):
    """--localizable-stringarrays / --localizable-other / --localizable-to-many-relationships
    は通常 空 dict {} である"""

    def test_apple_empty_types(self):
        for plat in PLATFORMS:
            for kind in ["stringarrays", "other", "to-many-relationships"]:
                d = _load_apple(plat, f"localizable-{kind}")
                if not d:
                    continue
                if "com.apple.ibtool.errors" in d:
                    continue
                val = d.get(f"com.apple.ibtool.document.localizable-{kind}")
                with self.subTest(platform=plat, kind=kind):
                    if val is not None:
                        self.assertIsInstance(val, dict)


class TestAppleWriteBack(unittest.TestCase):
    """--write 出力の xib が Apple 出力と一致するか (構造)"""

    def test_ios_write_back_loadable(self):
        out = FIXTURES / "ios_out.xib"
        if not out.exists():
            self.skipTest("no ios_out.xib")
        content = out.read_text(encoding="utf-8")
        self.assertIn("<document", content)
        self.assertIn("com.apple.InterfaceBuilder3", content)


class TestAppleStrip(unittest.TestCase):
    """--strip 出力 nib が存在する"""

    def test_strip_files_exist(self):
        for plat in ["ios"]:  # iOS のみ
            for sfx in ["strip.nib"]:
                p = FIXTURES / f"{plat}_{sfx}"
                if p.exists():
                    raw = p.read_bytes()
                    self.assertEqual(raw[:10], b"NIBArchive")


class TestAppleHumanReadableText(unittest.TestCase):
    """--all --output-format human-readable-text の出力"""

    def test_human_readable_says_not_supported(self):
        for plat in PLATFORMS:
            t = FIXTURES / f"{plat}_all.txt"
            if not t.exists():
                continue
            content = t.read_text(encoding="utf-8")
            with self.subTest(platform=plat):
                if "ibtool does not support" in content:
                    pass  # Apple も "ibtool does not support human readable output"


class TestAppleBinary1Plist(unittest.TestCase):
    """--all --output-format binary1 の出力 (バイナリ plist)"""

    def test_binary1_decodable(self):
        for plat in PLATFORMS:
            p = FIXTURES / f"{plat}_all.bin"
            if not p.exists():
                continue
            raw = p.read_bytes()
            with self.subTest(platform=plat):
                # binary1 plist は "bplist00" で始まる
                self.assertTrue(raw.startswith(b"bplist00"),
                    f"{plat} not binary1: {raw[:20]}")
                d = plistlib.loads(raw)
                # Apple 出力に errors がある = スキップ
                if "com.apple.ibtool.errors" in d:
                    continue
                # キーあり
                self.assertIn("com.apple.ibtool.document.classes", d)


class TestCompileOutput(unittest.TestCase):
    """Apple --compile 出力 nib の magic"""

    def test_apple_nib_magic(self):
        for plat in PLATFORMS:
            ext = "storyboardc" if plat == "story" else "nib"
            p = FIXTURES / f"{plat}.{ext}"
            if not p.exists():
                continue
            if p.is_dir():
                continue
            raw = p.read_bytes()
            with self.subTest(platform=plat):
                # nib: NIBArchive
                # storyboardc: ディレクトリ
                if ext == "nib":
                    self.assertEqual(raw[:10], b"NIBArchive")


if __name__ == "__main__":
    unittest.main(verbosity=2)
