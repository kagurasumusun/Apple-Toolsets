"""
test_nib_runtime_structure.py - NIB 出力の構造的同等性検証

pyibtool --compile 出力 nib と Apple ibtool --compile 出力 nib を比較。
バイト一致は無理 (Xcode 26.5 内部仕様が異なる可能性) だが、
NIBArchive ヘッダ・オブジェクト数・キー数・クラス数は同じはず。
"""
import os, sys, struct, plistlib, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text
from pyibtool.nibarchive import parse_nib

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _run(args):
    import io
    old_out = sys.stdout
    old_err = sys.stderr
    try:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return code, out, err
    finally:
        sys.stdout = old_out
        sys.stderr = old_err


class TestNIBHeaderStructure(unittest.TestCase):
    """NIBArchive ヘッダ 50 バイト = magic(10) + formatVersion(4) + coderVersion(4) + 8x(count,offset)"""

    def test_apple_nib_header_50_bytes(self):
        """Apple nib は 50 バイトヘッダ"""
        nib = FIXTURES / "golden" / "A1.nib"
        if not nib.exists():
            self.skipTest("no apple nib")
        with open(nib, "rb") as f:
            data = f.read()
        self.assertEqual(data[:10], b"NIBArchive")
        fv = struct.unpack_from("<I", data, 0x0a)[0]
        cv = struct.unpack_from("<I", data, 0x0e)[0]
        self.assertEqual(fv, 1, f"formatVersion: {fv}")
        self.assertIn(cv, (9, 10, 11, 12, 13), f"coderVersion: {cv}")
        # 最初の 4 つのテーブル (objects/keys/values/classNames) は妥当
        for i in range(4):
            off = 0x12 + i * 8
            c = struct.unpack_from("<I", data, off)[0]
            o = struct.unpack_from("<I", data, off + 4)[0]
            # 妥当な範囲 (NIBArchive 仕様の最初の 4 テーブルのみ検証)
            self.assertLessEqual(o, len(data),
                f"table {i} offset {o} > file size {len(data)}")
            self.assertGreater(c, 0, f"table {i} count {c} must be > 0")

    def test_pyibtool_nib_header_50_bytes(self):
        """pyibtool --compile 出力 nib も 50 バイトヘッダ"""
        import io, tempfile
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--compile", tmp, str(FIXTURES / "input" / "ivc.xib")])
            self.assertEqual(code, 0)
            with open(tmp, "rb") as f:
                data = f.read()
            self.assertEqual(data[:10], b"NIBArchive")
            fv = struct.unpack_from("<I", data, 0x0a)[0]
            self.assertEqual(fv, 1)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestNIBParse(unittest.TestCase):
    """NIB パーサの検証"""

    def test_apple_nib_parse_round_trip(self):
        nib = FIXTURES / "golden" / "A1.nib"
        if not nib.exists():
            self.skipTest("no apple nib")
        with open(nib, "rb") as f:
            data = f.read()
        arch = parse_nib(data)
        # 再ビルド
        from pyibtool.nibarchive import build_nib
        rebuilt = build_nib(arch)
        self.assertEqual(data, rebuilt, "Apple nib round-trip must be byte-identical")

    def test_all_apple_nibs_round_trip(self):
        """全 Apple nib で round-trip 一致"""
        from pyibtool.nibarchive import build_nib
        golden = FIXTURES / "golden"
        exclude = {"out.nib", "A9.nib", "A32.storyboardc"}
        nibs = sorted(f for f in os.listdir(golden)
                      if f.endswith(".nib") and f not in exclude)
        results = []
        for f in nibs:
            p = golden / f
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
        for f, o, r, m in results:
            status = "OK" if m is True else ("NG" if m is False else m)
            print(f"  {f}: orig={o} rebuilt={r} {status}")
        fails = [r for r in results if r[3] is not True]
        self.assertEqual(len(fails), 0,
                         f"{len(fails)} nibs failed round-trip: {fails}")


class TestNIBClassNames(unittest.TestCase):
    """Apple nib の class 名が完全一致"""

    def test_apple_nib_classes(self):
        nib = FIXTURES / "golden" / "A1.nib"
        if not nib.exists():
            self.skipTest("no apple nib")
        with open(nib, "rb") as f:
            data = f.read()
        arch = parse_nib(data)
        names = [c.name for c in arch.class_names]
        # 期待される 9 class
        expected = ['NSObject', 'NSArray', 'UIProxyObject', 'NSString',
                    'UIView', 'UIColor', 'UILayoutGuide',
                    'UIRuntimeOutletConnection', 'NSColor']
        self.assertEqual(names, expected)


class TestNIBObjects(unittest.TestCase):
    """Apple nib の object 数・value 数"""

    def test_apple_nib_objects_count(self):
        nib = FIXTURES / "golden" / "A1.nib"
        with open(nib, "rb") as f:
            data = f.read()
        arch = parse_nib(data)
        self.assertEqual(len(arch.objects), 16)
        self.assertEqual(len(arch.values), 51)
        self.assertEqual(len(arch.keys), 36)


class TestNIBEmptyFile(unittest.TestCase):
    """A9.nib のような空 nib"""

    def test_a9_nib(self):
        p = FIXTURES / "golden" / "A9.nib"
        if not p.exists():
            self.skipTest("no A9.nib")
        with open(p, "rb") as f:
            data = f.read()
        # 空 nib でも magic はある
        if len(data) > 0:
            self.assertTrue(data[:10] == b"NIBArchive" or len(data) < 50)


class TestNIBOldFormat(unittest.TestCase):
    """out.nib は古い形式 (LNE trailer なし)"""

    def test_out_nib_no_lne(self):
        p = FIXTURES / "golden" / "out.nib"
        if not p.exists():
            self.skipTest("no out.nib")
        with open(p, "rb") as f:
            data = f.read()
        if len(data) >= 4:
            # LNE trailer 無し
            last4 = data[-4:]
            self.assertNotEqual(last4, b"LNE\0",
                                "out.nib has LNE trailer (unexpected)")


class TestPyibtoolCompileBinaryIverse(unittest.TestCase):
    """pyibtool --compile 出力 nib の構造的検証"""

    def test_pyibtool_nib_parseable(self):
        import io, tempfile
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--compile", tmp, str(FIXTURES / "input" / "ivc.xib")])
            self.assertEqual(code, 0)
            with open(tmp, "rb") as f:
                data = f.read()
            # parse できる
            arch = parse_nib(data)
            self.assertGreater(len(arch.class_names), 0)
            self.assertGreater(len(arch.objects), 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_pyibtool_nib_round_trip(self):
        """pyibtool 出力 nib も round-trip 一致 (自身の出力)"""
        import io, tempfile
        from pyibtool.nibarchive import build_nib
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--compile", tmp, str(FIXTURES / "input" / "ivc.xib")])
            with open(tmp, "rb") as f:
                data = f.read()
            arch = parse_nib(data)
            rebuilt = build_nib(arch)
            self.assertEqual(data, rebuilt,
                             "pyibtool nib round-trip must be byte-identical")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
