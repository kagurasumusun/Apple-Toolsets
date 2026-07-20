"""
test_xcode_14_xib.py - Xcode 14+ 形式の xib 完全パーステスト

Xcode 14+ で導入された新機能 (customModuleProvider, customModule, viewControllerLayoutGuide 等) を含む
xib/storyboard をパースして全機能確認。
"""
import os, sys, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text, serialize_xib

FIXTURES = Path(__file__).parent.parent / "fixtures"
WEB = FIXTURES / "web"


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


class TestXcode14PlusFeatures(unittest.TestCase):
    """Xcode 14+ の新機能"""

    def setUp(self):
        if not WEB.exists():
            self.skipTest("no web fixtures")
        self.fixtures = list(WEB.glob("*.storyboard"))
        if not self.fixtures:
            self.skipTest("no web storyboards")

    def test_custom_module_provider(self):
        """customModule / customModuleProvider のパース"""
        for f in self.fixtures:
            with self.subTest(file=f.name):
                text = f.read_text(encoding="utf-8")
                doc = parse_xib_text(text)
                # customModule を持つ object を探す
                modules = set()
                for s in doc.scenes:
                    for o in s.objects:
                        if "customModule" in o.attributes:
                            modules.add(o.attributes["customModule"])
                self.assertGreater(len(modules), 0, f"no customModule in {f.name}")

    def test_view_controller_layout_guide(self):
        """viewControllerLayoutGuide / layoutGuides container のパース"""
        for f in self.fixtures:
            with self.subTest(file=f.name):
                text = f.read_text(encoding="utf-8")
                if "layoutGuide" not in text:
                    self.skipTest(f"no layoutGuide in {f.name}")
                doc = parse_xib_text(text)
                # 何か layout guide 系が含まれる
                has_guide = False
                def walk(o):
                    nonlocal has_guide
                    for c in o.children:
                        if "layoutGuide" in c.tag or "layoutGuides" == c.tag:
                            has_guide = True
                        walk(c)
                for s in doc.scenes:
                    for o in s.objects:
                        walk(o)
                self.assertTrue(has_guide, f"no layoutGuide in {f.name}")

    def test_scene_scenes_top_level(self):
        """<scenes>/<scene> トップレベル"""
        for f in self.fixtures:
            with self.subTest(file=f.name):
                text = f.read_text(encoding="utf-8")
                doc = parse_xib_text(text)
                self.assertEqual(doc.doc_type,
                    "com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB")

    def test_compile_xcode14_xib(self):
        """Xcode 14+ xib の compile"""
        for f in self.fixtures:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".storyboardc", delete=False) as t:
                    tmp = t.name
                try:
                    code, _ = _run(["--compile", tmp, str(f)])
                    self.assertEqual(code, 0, f"compile failed for {f.name}")
                    import os
                    self.assertTrue(os.path.isdir(tmp) or os.path.getsize(tmp) > 0)
                finally:
                    import shutil
                    if os.path.exists(tmp):
                        if os.path.isdir(tmp):
                            shutil.rmtree(tmp)
                        else:
                            os.unlink(tmp)


class TestRoundTripPreservesCustomModule(unittest.TestCase):
    """round-trip で customModule が保持されるか"""

    def setUp(self):
        if not WEB.exists():
            self.skipTest("no web fixtures")
        self.fixtures = list(WEB.glob("*.storyboard"))

    def test_custom_module_preserved(self):
        for f in self.fixtures[:3]:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".storyboard", delete=False) as t:
                    tmp = t.name
                try:
                    code, _ = _run(["--write", tmp, str(f)])
                    self.assertEqual(code, 0)
                    text2 = open(tmp).read()
                    # customModule があるなら保持
                    if "customModule=" in f.read_text():
                        self.assertIn("customModule=", text2,
                            f"customModule not preserved in {f.name}")
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
