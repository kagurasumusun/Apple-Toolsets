"""
test_nib_xib_roundtrip_4stage.py - 4 段 round-trip の完全検証

xib → nib → xib → nib の 4 段 round-trip で構造的同等性確認。
"""
import os, sys, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.nib2xib import nib2xib
from pyibtool.nibarchive import parse_nib
from pyibtool.xibdoc import parse_xib_text, serialize_xib

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


class TestFourStageRoundTrip(unittest.TestCase):
    """xib → nib → xib → nib の 4 段 round-trip"""

    def setUp(self):
        self.xib_path = FIXTURES / "ios.xib"
        if not self.xib_path.exists():
            self.skipTest("no ios.xib")
        self.nib1 = None
        self.nib2 = None
        self.xib2 = None

    def tearDown(self):
        for p in [self.nib1, self.nib2, self.xib2]:
            if p and os.path.exists(p):
                os.unlink(p)

    def test_four_stage_round_trip(self):
        """xib → nib1 → xib2 → nib2 の 4 段 round-trip"""
        # Step 1: xib → nib1
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            self.nib1 = f.name
        code, _ = _run(["--compile", self.nib1, str(self.xib_path)], binary=True)
        self.assertEqual(code, 0, "step 1 failed")
        self.assertGreater(os.path.getsize(self.nib1), 0)

        # nib1 parse
        arch1 = parse_nib(open(self.nib1, "rb").read())
        n_classes1 = len(arch1.class_names)
        n_objects1 = len(arch1.objects)
        print(f"  nib1: {n_classes1} classes, {n_objects1} objects")

        # Step 2: nib1 → xib2
        doc2 = nib2xib(arch1)
        text2 = serialize_xib(doc2)
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False, mode="w") as f:
            f.write(text2)
            self.xib2 = f.name

        # xib2 parse 可能
        doc2_parsed = parse_xib_text(text2)
        self.assertGreater(len(doc2_parsed.objects), 0)

        # Step 3: xib2 → nib2
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            self.nib2 = f.name
        code, _ = _run(["--compile", self.nib2, self.xib2], binary=True)
        self.assertEqual(code, 0, "step 3 failed")
        self.assertGreater(os.path.getsize(self.nib2), 0)

        # nib2 parse
        arch2 = parse_nib(open(self.nib2, "rb").read())
        n_classes2 = len(arch2.class_names)
        n_objects2 = len(arch2.objects)
        print(f"  nib2: {n_classes2} classes, {n_objects2} objects")

        # 元の nib1 と同じ object count
        self.assertEqual(n_objects1, n_objects2,
                         f"object count mismatch: nib1={n_objects1} nib2={n_objects2}")

        # 主要 class (UIView, UIProxyObject, NSObject 等) は保持される
        classes2 = set(c.name for c in arch2.class_names)
        self.assertIn("UIView", classes2)
        self.assertIn("UIProxyObject", classes2)
        self.assertIn("NSObject", classes2)
        self.assertIn("NSString", classes2)


class TestXib2XibRoundTrip(unittest.TestCase):
    """xib → xib (parse → serialize) の round-trip"""

    def setUp(self):
        self.xib_path = FIXTURES / "ios.xib"
        if not self.xib_path.exists():
            self.skipTest("no ios.xib")

    def test_xib_round_trip_preserves_structure(self):
        text1 = open(self.xib_path).read()
        doc1 = parse_xib_text(text1)
        text2 = serialize_xib(doc1)
        doc2 = parse_xib_text(text2)
        # 同じ object 数
        self.assertEqual(len(doc1.objects), len(doc2.objects))
        # 同じ id
        ids1 = sorted(o.id for o in doc1.objects)
        ids2 = sorted(o.id for o in doc2.objects)
        self.assertEqual(ids1, ids2)
        # 同じ tag
        tags1 = sorted(o.tag for o in doc1.objects)
        tags2 = sorted(o.tag for o in doc2.objects)
        self.assertEqual(tags1, tags2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
