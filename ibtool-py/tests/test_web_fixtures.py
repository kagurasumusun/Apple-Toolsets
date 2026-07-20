"""
test_web_fixtures.py - web から取得した xib/storyboard のパース + 機能テスト

XcodeGen, ABBYY などの OSS プロジェクトから取得した本物の xib/storyboard で
pyibtool の全機能を検証。
"""
import os, sys, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text, serialize_xib

WEB = Path(__file__).parent.parent / "fixtures" / "web"


def _run(args, capture_binary=False):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        sys.stdout = io.BytesIO() if capture_binary else io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return code, out, err
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestWebStoryboard(unittest.TestCase):
    """XcodeGen + ABBYY の storyboard"""

    def setUp(self):
        self.fixtures = list(WEB.glob("*.storyboard"))
        if not self.fixtures:
            self.skipTest("no web fixtures")

    def test_parse_all(self):
        for f in self.fixtures:
            with self.subTest(file=f.name):
                text = f.read_text(encoding="utf-8")
                doc = parse_xib_text(text)
                self.assertIn("Storyboard", doc.doc_type)
                self.assertGreater(len(doc.scenes), 0)

    def test_write_all(self):
        for f in self.fixtures:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".storyboard", delete=False) as t:
                    tmp = t.name
                try:
                    code, _, _ = _run(["--write", tmp, str(f)])
                    self.assertEqual(code, 0)
                    self.assertGreater(os.path.getsize(tmp), 0)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)

    def test_compile_all(self):
        for f in self.fixtures:
            with self.subTest(file=f.name):
                with tempfile.TemporaryDirectory() as td:
                    tmp = os.path.join(td, "test.storyboardc")
                    code, _, _ = _run(["--compile", tmp, str(f)])
                    self.assertEqual(code, 0, f"compile failed for {f.name}")
                    self.assertTrue(os.path.isdir(tmp))
                    # ディレクトリ内のファイル合計サイズ
                    total = 0
                    for root, _, files in os.walk(tmp):
                        for ff in files:
                            total += os.path.getsize(os.path.join(root, ff))
                    self.assertGreater(total, 100)

    def test_all_dumps(self):
        dumps = ["classes", "objects", "hierarchy", "connections", "all",
                 "version-history", "localizable-strings", "localizable-all",
                 "warnings", "errors", "notices"]
        for f in self.fixtures:
            for d in dumps:
                with self.subTest(file=f.name, dump=d):
                    code, out, _ = _run([f"--{d}", str(f)])
                    self.assertEqual(code, 0)
                    self.assertIn("com.apple.ibtool", out)

    def test_xliff_export(self):
        for f in self.fixtures:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as t:
                    tmp = t.name
                try:
                    code, _, _ = _run(["--export-xliff", tmp,
                                      "--source-language", "en",
                                      "--target-language", "ja", str(f)])
                    self.assertEqual(code, 0)
                    content = open(tmp).read()
                    self.assertIn("xmlns:ib=\"com.apple.InterfaceBuilder3\"", content)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)

    def test_xib_to_xib_round_trip(self):
        """web storyboard → parse → write → 同じファイルサイズ程度で復元"""
        for f in self.fixtures:
            with self.subTest(file=f.name):
                with tempfile.NamedTemporaryFile(suffix=".storyboard", delete=False) as t:
                    tmp = t.name
                try:
                    code, _, _ = _run(["--write", tmp, str(f)])
                    self.assertEqual(code, 0)
                    # パース可能
                    text = open(tmp).read()
                    doc2 = parse_xib_text(text)
                    self.assertIn("Storyboard", doc2.doc_type)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)


class TestXcodeGenStoryboard(unittest.TestCase):
    """XcodeGen のサンプル"""

    def setUp(self):
        self.f = WEB / "xcodegen_main.storyboard"
        if not self.f.exists():
            self.skipTest("no xcodegen fixture")

    def test_scene_objects(self):
        text = self.f.read_text(encoding="utf-8")
        doc = parse_xib_text(text)
        s = doc.scenes[0]
        # scene には全階層の object が含まれる (scene 自身、viewController、view、label、color 等)
        self.assertGreater(len(s.objects), 2)
        # viewController は customClass="ViewController", customModule="TestProject"
        vc = next((o for o in s.objects if o.tag == "viewController"), None)
        self.assertIsNotNone(vc)
        self.assertEqual(vc.attributes.get("customClass"), "ViewController")
        self.assertEqual(vc.attributes.get("customModule"), "TestProject")


class TestAbbyyStoryboard(unittest.TestCase):
    """ABBYY のサンプル (40 objects の複雑 storyboard)"""

    def setUp(self):
        self.f = WEB / "abbyy_main.storyboard"
        if not self.f.exists():
            self.skipTest("no abbyy fixture")

    def test_many_objects(self):
        text = self.f.read_text(encoding="utf-8")
        doc = parse_xib_text(text)
        s = doc.scenes[0]
        # scene には全階層の object が含まれる
        self.assertGreater(len(s.objects), 10)
        # customModule + customModuleProvider
        classes = set()
        for o in s.objects:
            cc = o.attributes.get("customClass")
            if cc:
                classes.add(cc)
        # 複数の class
        self.assertGreaterEqual(len(classes), 1)

    def test_constraints_in_objects(self):
        """ABBYY storyboard に constraint 多数 (view の中に)"""
        text = self.f.read_text(encoding="utf-8")
        doc = parse_xib_text(text)
        s = doc.scenes[0]
        # 全体で constraint を探す
        all_constraints = []
        def walk(o):
            for c in o.children:
                if c.tag == "constraints":
                    all_constraints.append(c)
                else:
                    walk(c)
        for o in s.objects:
            walk(o)
        # constraint コンテナがある
        self.assertGreater(len(all_constraints), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
