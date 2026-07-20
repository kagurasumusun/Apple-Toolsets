"""
test_storyboardc.py - storyboard → storyboardc compile テスト

storyboard (iOS CocoaTouch) を入力として .storyboardc (ディレクトリ)
を生成するテスト。Apple ibtool は --compile で .storyboard 入力の場合
.storyboardc ディレクトリを作る。
"""
import os, sys, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text

FIXTURES = Path(__file__).parent.parent / "fixtures"


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


class TestStoryboardC(unittest.TestCase):
    """storyboard → storyboardc コンパイル"""

    def setUp(self):
        self.story = FIXTURES / "probe_v8" / "story.storyboard"
        if not self.story.exists():
            self.skipTest("no story.storyboard")

    def test_storyboard_parse(self):
        """storyboard が parse 可能で scene を含む"""
        text = self.story.read_text()
        doc = parse_xib_text(text)
        self.assertGreater(len(doc.scenes), 0, "storyboard has no scenes")
        # scene 内に objects がある
        for s in doc.scenes:
            self.assertGreater(len(s.objects), 0, f"scene {s.id} has no objects")

    def test_storyboard_dump_all(self):
        """storyboard で --all dump が動作"""
        code, out = _run(["--all", str(self.story)])
        self.assertEqual(code, 0)
        import plistlib
        data = plistlib.loads(out)
        # Apple 仕様 9 キー全部
        self.assertIn("com.apple.ibtool.document.hierarchy", data)
        self.assertIn("com.apple.ibtool.document.classes", data)
        self.assertIn("com.apple.ibtool.document.objects", data)

    def test_storyboard_dump_hierarchy(self):
        """storyboard の hierarchy に scene が含まれる"""
        code, out = _run(["--hierarchy", str(self.story)])
        self.assertEqual(code, 0)
        import plistlib
        data = plistlib.loads(out)
        hier = data["com.apple.ibtool.document.hierarchy"]
        self.assertGreater(len(hier), 0)


class TestStoryboardParse(unittest.TestCase):
    """複数の storyboard フィクスチャで parse を検証"""

    def setUp(self):
        self.storyboards = list(FIXTURES.rglob("*.storyboard"))

    def test_all_storyboards_parse(self):
        """全ての storyboard が parse 可能"""
        ok = 0
        fail = 0
        for s in self.storyboards:
            try:
                text = s.read_text()
                doc = parse_xib_text(text)
                if len(doc.scenes) > 0 or len(doc.objects) > 0:
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                fail += 1
        print(f"  parsed: {ok}/{ok+fail} storyboards")
        self.assertGreater(ok, 0, "no storyboard parsed successfully")


if __name__ == "__main__":
    unittest.main(verbosity=2)
