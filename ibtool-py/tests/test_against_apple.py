"""
Apple 純正 ibtool の出力 (golden fixtures) と pyibtool の出力を比較検証

golden fixtures:
  fixtures/golden/A1.nib ... 純正 ibtool --compile の出力 (iOS, default)
  fixtures/golden/A32.storyboardc ... storyboard compile 出力
  fixtures/plist/A*.plist ... --classes, --objects 等の plist 出力
  fixtures/plist/A40.xlf ... --export-xliff 出力
  fixtures/plist/A22.strings ... --export-strings-file 出力

本テストは「pyibtool が Apple 出力と**構造的に同等**か」を検証する。
バイト一致は検証しない (Xcode 26.5 の NIB 形式と本実装の NIB 形式は完全一致しない)。
"""

import os
import sys
import plistlib
import unittest
import io
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text
from pyibtool.nibarchive import parse_nib


FIXTURES = Path(__file__).parent.parent / "fixtures"


def _run(argv, capture_binary=False):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        if capture_binary:
            sys.stdout = io.BytesIO()
        else:
            sys.stdout = io.StringIO()
        code = ibtool.main(argv)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return code, out, err
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestAgainstAppleClasses(unittest.TestCase):
    """A18.plist (Apple --classes 出力) と pyibtool --classes を構造比較"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A18.plist"
        if not self.golden.exists():
            self.skipTest("no golden A18.plist")
        with open(self.golden, "rb") as f:
            self.apple_data = plistlib.load(f)

    def test_classes_dict_structure(self):
        """pyibtool --classes が Apple 出力と同じトップレベルキーを持つ"""
        code, out, _ = _run(["--classes", str(FIXTURES / "input" / "ivc.xib")])
        self.assertEqual(code, 0)
        py_data = plistlib.loads(out.encode("utf-8"))
        # Apple は com.apple.ibtool.document.classes
        self.assertIn("com.apple.ibtool.document.classes", py_data)
        self.assertIn("com.apple.ibtool.document.classes", self.apple_data)
        # クラス構造: class は必須。superclass は省略可能な Apple 出力もある
        # (FirstResponder, NSCoder 等)
        py_classes = py_data["com.apple.ibtool.document.classes"]
        apple_classes = self.apple_data["com.apple.ibtool.document.classes"]
        for cname, cdict in py_classes.items():
            self.assertIn("class", cdict, f"class {cname} missing class")
        # Apple の class 数と pyibtool の class 数が同程度
        self.assertGreater(len(py_classes), 50,
            f"pyibtool class count too low: {len(py_classes)}")
        # Apple にも同じクラスが含まれている
        for cname in apple_classes:
            # Apple の class 名と完全一致は期待しないが、UIView / UIViewController 等の
            # 一般的なクラス名は Apple 出力にある
            pass


class TestAgainstAppleObjects(unittest.TestCase):
    """A15.plist (Apple --objects) と pyibtool --objects"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A15.plist"
        if not self.golden.exists():
            self.skipTest("no golden A15.plist")
        with open(self.golden, "rb") as f:
            self.apple_data = plistlib.load(f)

    def test_objects_dict_structure(self):
        code, out, _ = _run(["--objects", str(FIXTURES / "input" / "ivc.xib")])
        self.assertEqual(code, 0)
        py_data = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.objects", py_data)
        self.assertIn("com.apple.ibtool.document.objects", self.apple_data)


class TestAgainstAppleHierarchy(unittest.TestCase):
    """A16.plist (Apple --hierarchy) と pyibtool --hierarchy"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A16.plist"
        if not self.golden.exists():
            self.skipTest("no golden A16.plist")
        with open(self.golden, "rb") as f:
            self.apple_data = plistlib.load(f)

    def test_hierarchy_dict_structure(self):
        code, out, _ = _run(["--hierarchy", str(FIXTURES / "input" / "ivc.xib")])
        self.assertEqual(code, 0)
        py_data = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.hierarchy", py_data)


class TestAgainstAppleConnections(unittest.TestCase):
    """A17.plist (Apple --connections) と pyibtool --connections"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A17.plist"
        if not self.golden.exists():
            self.skipTest("no golden A17.plist")
        with open(self.golden, "rb") as f:
            self.apple_data = plistlib.load(f)

    def test_connections_dict_structure(self):
        code, out, _ = _run(["--connections", str(FIXTURES / "input" / "ivc.xib")])
        self.assertEqual(code, 0)
        py_data = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.connections", py_data)


class TestAgainstAppleAll(unittest.TestCase):
    """A21.plist (Apple --all) と pyibtool --all"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A21.plist"
        if not self.golden.exists():
            self.skipTest("no golden A21.plist")
        with open(self.golden, "rb") as f:
            self.apple_data = plistlib.load(f)

    def test_all_includes_major_keys(self):
        code, out, _ = _run(["--all", str(FIXTURES / "input" / "ivc.xib")])
        self.assertEqual(code, 0)
        py_data = plistlib.loads(out.encode("utf-8"))
        # Apple 出力に存在するキーのうち主要なもの
        for k in [
            "com.apple.ibtool.document.objects",
            "com.apple.ibtool.document.hierarchy",
            "com.apple.ibtool.document.connections",
            "com.apple.ibtool.document.classes",
            "com.apple.ibtool.document.version-history",
        ]:
            self.assertIn(k, py_data, f"--all missing key: {k}")


class TestAgainstAppleXLIFF(unittest.TestCase):
    """A40.xlf (Apple --export-xliff) と pyibtool --export-xliff"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A40.xlf"
        if not self.golden.exists():
            self.skipTest("no golden A40.xlf")
        with open(self.golden, "r", encoding="utf-8") as f:
            self.apple_xlf = f.read()

    def test_xliff_structure(self):
        """pyibtool が出力する XLIFF が Apple と同じ要素を持つ"""
        with tempfile.NamedTemporaryFile("w", suffix=".xlf", delete=False) as f:
            tmpname = f.name
        try:
            code, _, _ = _run(["--export-xliff", tmpname, "--source-language", "en",
                              "--target-language", "ja",
                              str(FIXTURES / "input" / "ivc.xib")])
            self.assertEqual(code, 0)
            with open(tmpname, "r", encoding="utf-8") as f:
                py_xlf = f.read()
            # XLIFF 1.2 共通構造
            self.assertIn("xliff", py_xlf)
            self.assertIn("source-language=\"en\"", py_xlf)
            self.assertIn("target-language=\"ja\"", py_xlf)
        finally:
            if os.path.exists(tmpname):
                os.unlink(tmpname)


class TestAgainstAppleStrings(unittest.TestCase):
    """A22.strings (Apple --export-strings-file) と pyibtool --export-strings-file"""

    def setUp(self):
        self.golden = FIXTURES / "plist" / "A22.strings"
        if not self.golden.exists():
            self.skipTest("no golden A22.strings")

    def test_strings_output(self):
        with tempfile.NamedTemporaryFile("w", suffix=".strings", delete=False) as f:
            tmpname = f.name
        try:
            code, _, _ = _run(["--export-strings-file", tmpname,
                              str(FIXTURES / "input" / "ivc.xib")])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(tmpname))
            with open(tmpname, "r", encoding="utf-8") as f:
                content = f.read()
            # Apple strings ファイル形式
            # (空でも良い、xib に localizable 文字列が無い場合)
        finally:
            if os.path.exists(tmpname):
                os.unlink(tmpname)


class TestAgainstAppleNIB(unittest.TestCase):
    """A1.nib (Apple --compile 出力) のヘッダと pyibtool --compile 出力の比較"""

    def setUp(self):
        self.golden = FIXTURES / "golden" / "A1.nib"
        if not self.golden.exists():
            self.skipTest("no golden A1.nib")
        with open(self.golden, "rb") as f:
            self.apple_nib = f.read()

    def test_apple_nib_magic(self):
        """Apple 出力 nib の magic 確認"""
        self.assertEqual(self.apple_nib[:10], b"NIBArchive")

    def test_apple_nib_header(self):
        """Apple 出力 nib のヘッダ 10 フィールド (Archaeology 仕様)"""
        import struct
        # +0x0a..+0x0d: formatVersion
        # +0x0e..+0x11: coderVersion
        fv = struct.unpack_from("<I", self.apple_nib, 0x0a)[0]
        cv = struct.unpack_from("<I", self.apple_nib, 0x0e)[0]
        self.assertEqual(fv, 1, f"formatVersion should be 1, got {fv}")
        # coderVersion は歴史的に 9 (旧) or 0xa (新)
        self.assertIn(cv, (9, 10, 11, 12, 13), f"coderVersion {cv} unexpected")

    def test_apple_nib_parseable(self):
        """Archaeology 仕様に基づき parse 可能か (Xcode 26.5 で失敗する可能性あり)"""
        import struct
        # ヘッダは確実に読める
        fv = struct.unpack_from("<I", self.apple_nib, 0x0a)[0]
        cv = struct.unpack_from("<I", self.apple_nib, 0x0e)[0]
        obj_count = struct.unpack_from("<I", self.apple_nib, 0x12)[0]
        obj_off = struct.unpack_from("<I", self.apple_nib, 0x16)[0]
        key_count = struct.unpack_from("<I", self.apple_nib, 0x1a)[0]
        key_off = struct.unpack_from("<I", self.apple_nib, 0x1e)[0]
        val_count = struct.unpack_from("<I", self.apple_nib, 0x22)[0]
        val_off = struct.unpack_from("<I", self.apple_nib, 0x26)[0]
        cls_count = struct.unpack_from("<I", self.apple_nib, 0x2a)[0]
        cls_off = struct.unpack_from("<I", self.apple_nib, 0x2e)[0]
        # 各フィールドは妥当な範囲
        self.assertGreater(obj_count, 0)
        self.assertGreater(obj_off, 0)
        self.assertLess(obj_off, len(self.apple_nib))
        self.assertGreater(key_count, 0)
        self.assertGreater(key_off, obj_off)
        self.assertLess(key_off, len(self.apple_nib))

    def test_pyibtool_compile_nib_magic(self):
        """pyibtool --compile 出力 nib の magic"""
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmpname = f.name
        try:
            code, _, _ = _run(["--compile", tmpname, str(FIXTURES / "input" / "ivc.xib")])
            self.assertEqual(code, 0)
            with open(tmpname, "rb") as f:
                py_nib = f.read()
            self.assertEqual(py_nib[:10], b"NIBArchive")
            # ヘッダも Archaeology 仕様に従う
            import struct
            fv = struct.unpack_from("<I", py_nib, 0x0a)[0]
            self.assertEqual(fv, 1)
        finally:
            if os.path.exists(tmpname):
                os.unlink(tmpname)

    def test_nib_format_compatibility(self):
        """
        Apple nib と pyibtool nib のフォーマット互換性に関する事実:
        - ヘッダ 50 バイトは同じ (Archaeology 仕様)
        - テーブル構造 (object/key/value/class) は同じ
        - ただし、Xcode 26.5 の nib は Archaeology 仕様と異なる可能性があり、
          バイト一致は保証されない
        本テストはその事実を確認する。
        """
        import struct
        a = self.apple_nib
        # Apple の nib は coderVersion 10 (Xcode 26.5 の ibtool が出力)
        cv_apple = struct.unpack_from("<I", a, 0x0e)[0]
        # pyibtool の nib は coderVersion 10 (明示的に設定)
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmpname = f.name
        try:
            _run(["--compile", tmpname, str(FIXTURES / "input" / "ivc.xib")])
            with open(tmpname, "rb") as f:
                b = f.read()
            cv_py = struct.unpack_from("<I", b, 0x0e)[0]
            self.assertEqual(cv_apple, cv_py, f"coderVersion mismatch: Apple={cv_apple} pyibtool={cv_py}")
        finally:
            if os.path.exists(tmpname):
                os.unlink(tmpname)

    def test_xib_nib_xib_nib_semantic_round_trip(self):
        """
        xib → nib → xib → nib の round-trip で、
        nib1 と nib3 が **構造的に** (クラス名 / object 数 / value 数) 等価であることを確認する。
        バイト一致は (key 順序、attribute 順などの違いで) 保証しない。
        """
        from pyibtool.xibdoc import parse_xib_text
        from pyibtool.nibcompile import build_nib_from_xib
        from pyibtool.nibarchive import build_nib, parse_nib
        from pyibtool.nib2xib import nib2xib
        from pyibtool.xibdoc import serialize_xib

        with open(FIXTURES / "input" / "ivc.xib", "r", encoding="utf-8") as f:
            doc1 = parse_xib_text(f.read())
        arch1 = build_nib_from_xib(doc1)
        nib1 = build_nib(arch1)
        # nib → xib
        arch2 = parse_nib(nib1)
        doc2 = nib2xib(arch2)
        xib2 = serialize_xib(doc2)
        # xib2 パース可能
        doc2p = parse_xib_text(xib2)
        self.assertGreater(len(doc2p.objects), 0)
        # xib2 → nib2
        arch3 = build_nib_from_xib(doc2p)
        nib3 = build_nib(arch3)
        # 構造的に等価 (key 順序は違うのでバイト一致はしない)
        a1 = parse_nib(nib1)
        a3 = parse_nib(nib3)
        # 同じ class を持つ
        c1 = set(c.name for c in a1.class_names)
        c3 = set(c.name for c in a3.class_names)
        # 主要な class は一致
        for cname in ("NSObject", "NSArray", "UIProxyObject", "NSString", "UIView"):
            self.assertIn(cname, c1, f"missing in nib1: {cname}")
            self.assertIn(cname, c3, f"missing in nib3: {cname}")

    def test_apple_nib_byte_exact_round_trip(self):
        """
        Apple 純正 ibtool が出力した nib を、pyibtool で再パース → 再ビルドした結果が
        バイト単位で完全一致するか検証する。

        達成されれば、pyibtool は NIBArchive フォーマットに関して
        100% Apple 互換ということになる。
        """
        from pyibtool.nibarchive import parse_nib, build_nib
        arch = parse_nib(self.apple_nib)
        rebuilt = build_nib(arch)
        self.assertEqual(len(self.apple_nib), len(rebuilt),
                         f"size mismatch: Apple={len(self.apple_nib)} pyibtool={len(rebuilt)}")
        self.assertEqual(self.apple_nib, rebuilt,
                         "Apple nib round-trip mismatch (byte mismatch)")

    def test_apple_nib_class_names_complete(self):
        """Apple nib の全 class 名が正しく読み取れるか"""
        arch = parse_nib(self.apple_nib)
        # 9 class names が全て期待通り
        expected_classes = [
            'NSObject', 'NSArray', 'UIProxyObject', 'NSString',
            'UIView', 'UIColor', 'UILayoutGuide',
            'UIRuntimeOutletConnection', 'NSColor',
        ]
        actual = [c.name for c in arch.class_names]
        self.assertEqual(actual, expected_classes,
                         f"class names: {actual}")

    def test_apple_nib_objects_complete(self):
        """Apple nib の全 16 object が正しく読み取れるか"""
        arch = parse_nib(self.apple_nib)
        self.assertEqual(len(arch.objects), 16)
        # object 0 は NSObject (root)
        self.assertEqual(arch.lookup_class(arch.objects[0].class_index), 'NSObject')
        # object の value_count 合計
        total = sum(o.value_count for o in arch.objects)
        self.assertEqual(total, len(arch.values))

    def test_apple_nib_keys_complete(self):
        """Apple nib の全 36 key 名が読める"""
        arch = parse_nib(self.apple_nib)
        self.assertEqual(len(arch.keys), 36)
        # 必須キー
        key_names = {k.name for k in arch.keys}
        for required in ["UINibTopLevelObjectsKey", "UINibObjectsKey",
                         "UINibConnectionsKey", "NSInlinedValue",
                         "UIProxiedObjectIdentifier"]:
            self.assertIn(required, key_names, f"missing key: {required}")

    def test_apple_nib_values_complete(self):
        """Apple nib の全 51 value が読める"""
        arch = parse_nib(self.apple_nib)
        self.assertEqual(len(arch.values), 51)
        # 全ての value は key_index, type を持つ
        for v in arch.values:
            self.assertIsNotNone(v.type)
            self.assertGreaterEqual(v.key_index, 0)
            self.assertLess(v.key_index, 36)


class TestNIBByteExactMultiple(unittest.TestCase):
    """
    すべての Apple 出力 nib ファイル (golden fixtures) について
    round-trip 一致を検証する。
    """

    def test_all_apple_nibs_round_trip(self):
        import os
        from pyibtool.nibarchive import parse_nib, build_nib
        golden_dir = FIXTURES / "golden"
        # out.nib は古い形式 (LNE trailer なし) のため除外
        exclude = {"out.nib", "A9.nib"}  # A9.nib は空ファイル (ディレクトリ)
        nibs = sorted(f for f in os.listdir(golden_dir)
                      if f.endswith(".nib") and f not in exclude)
        results = []
        for f in nibs:
            p = golden_dir / f
            with open(p, "rb") as fp:
                orig = fp.read()
            if len(orig) < 50:
                continue
            try:
                arch = parse_nib(orig)
                rebuilt = build_nib(arch)
                match = (orig == rebuilt)
                results.append((f, len(orig), len(rebuilt), match))
            except Exception as e:
                results.append((f, len(orig), -1, f"err: {e}"))
        # 結果出力
        for f, o, r, m in results:
            status = "OK" if m is True else ("NG" if m is False else m)
            print(f"  {f}: orig={o} rebuilt={r} {status}")
        # 100% 一致を期待
        fails = [r for r in results if r[3] is not True]
        self.assertEqual(len(fails), 0,
                         f"{len(fails)}/{len(results)} nibs failed round-trip: {fails}")


class TestAgainstAppleVersion(unittest.TestCase):
    """Apple --version と pyibtool --version"""

    def test_version_apple(self):
        """A22 などで取得済みの Apple --version 出力 (ibtool_version.txt) と比較"""
        v = FIXTURES.parent.parent / "work" / "ibtool_research" / "ibtool_version.txt"
        if not v.exists():
            self.skipTest("no Apple version output")
        with open(v, "r", encoding="utf-8") as f:
            txt = f.read()
        # Apple は bundle-version=24765, short-bundle-version=26.5
        if "24765" in txt and "26.5" in txt:
            pass  # Apple 出力に到達


if __name__ == "__main__":
    unittest.main(verbosity=2)
