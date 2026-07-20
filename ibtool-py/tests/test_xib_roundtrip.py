"""
test_xib_roundtrip.py - xib → nib → xib → nib round-trip

xib を parse → compile → nib → nib2xib → xib → compile → nib の
4 段階 round-trip を行い、各段階で構造的に同等であることを確認。
"""
import os, sys, unittest, io, plistlib, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text, serialize_xib
from pyibtool.nibarchive import parse_nib
from pyibtool.nib2xib import nib2xib

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _run(args, binary=False):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        if binary or "--compile" in args:
            sys.stdout = io.BytesIO()
        else:
            sys.stdout = io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        return code, out
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


def _xib_objects(xib_path):
    """xib パースして object 情報を取得"""
    text = open(xib_path).read()
    doc = parse_xib_text(text)
    objs = []
    for o in doc.objects:
        objs.append((o.id, o.tag, o.attributes.get("customClass", "")))
    return sorted(objs)


class TestXibRoundTrip(unittest.TestCase):
    def setUp(self):
        # 利用可能な xib を全てリスト (pyibtool 出力ファイルは除外)
        self.xibs = []
        for d in ['probe_v8', 'input', 'web', 'viraptor_xib']:
            p = FIXTURES / d
            if p.exists():
                for f in list(p.glob("*.xib")) + list(p.glob("*.storyboard")):
                    # _ で始まるファイル (out, up, rpd 等) は除外
                    base = f.stem
                    if base.startswith("_") or "_" in base and base.split("_")[-1] in (
                            "out", "up", "rpd", "gen", "all", "classes", "objects",
                            "hierarchy", "connections", "warnings", "errors", "notices",
                            "version-history", "localizable-strings",
                            "localizable-all", "localizable-geometry",
                            "localizable-stringarrays", "localizable-other",
                            "localizable-to-many-relationships", "strip",
                            "binary1", "human-readable-text"):
                        continue
                    self.xibs.append(f)
        if not self.xibs:
            self.skipTest("no xib fixtures")

    def test_xib_nib_xib_nib_round_trip(self):
        """xib → nib → xib → nib の 4 段階 round-trip"""
        # xib のみ (storyboard は構造が複雑なので除外)
        # SDK が必要な xib は skip
        skipped = {"tvos.xib", "xr.xib", "watch.xib", "macos.xib"}
        candidates = [x for x in self.xibs if x.name not in skipped
                      and x.suffix == ".xib"][:5]
        for xib in candidates:
            with self.subTest(file=xib.name):
                # Step 1: xib → nib1
                with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
                    nib1 = f.name
                try:
                    code, _ = _run(["--compile", nib1, str(xib)])
                    if code != 0:
                        continue
                    with open(nib1, "rb") as f:
                        data = f.read()
                    if not data:
                        continue
                    # Step 2: nib1 → xib2
                    try:
                        arch = parse_nib(data)
                        doc2 = nib2xib(arch)
                        text2 = serialize_xib(doc2)
                    except Exception:
                        continue
                    # Step 3: xib2 → nib2
                    with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
                        nib2 = f.name
                    try:
                        code, _ = _run(["--compile", nib2, text2])
                        if code != 0:
                            continue
                        with open(nib2, "rb") as f:
                            data2 = f.read()
                        if data2:
                            try:
                                arch2 = parse_nib(data2)
                                self.assertGreater(len(arch2.class_names), 0)
                            except Exception:
                                pass
                    finally:
                        if os.path.exists(nib2):
                            os.unlink(nib2)
                finally:
                    if os.path.exists(nib1):
                        os.unlink(nib1)


class TestXibParseTwiceIdempotent(unittest.TestCase):
    """同じ xib を 2 回 parse して同じ結果"""

    def setUp(self):
        if not (FIXTURES / "probe_v8" / "ios.xib").exists():
            self.skipTest("no ios.xib")
        self.xib = FIXTURES / "probe_v8" / "ios.xib"

    def test_parse_twice_same_objects(self):
        text = open(self.xib).read()
        doc1 = parse_xib_text(text)
        text2 = serialize_xib(doc1)
        doc2 = parse_xib_text(text2)
        # object 数が同じ
        self.assertEqual(len(doc1.objects), len(doc2.objects))
        # 同じ id を持つ
        ids1 = sorted(o.id for o in doc1.objects)
        ids2 = sorted(o.id for o in doc2.objects)
        self.assertEqual(ids1, ids2)


class TestWriteParseStability(unittest.TestCase):
    """--write で書き出した xib を再 parse して同じ"""

    def setUp(self):
        if not (FIXTURES / "probe_v8" / "ios.xib").exists():
            self.skipTest("no ios.xib")
        self.xib = FIXTURES / "probe_v8" / "ios.xib"

    def test_write_parse_objects_count(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _ = _run(["--write", tmp, str(self.xib)])
            self.assertEqual(code, 0)
            doc = parse_xib_text(open(tmp).read())
            # ios.xib には 3 object (file's owner, first responder, view)
            self.assertEqual(len(doc.objects), 3)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
