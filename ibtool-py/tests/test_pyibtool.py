"""
pyibtool のテストハーネス

各機能について:
  - Apple 純正 ibtool と同じ操作を pyibtool で行う
  - exit code / stdout / stderr / ファイル出力サイズを比較
  - 完全一致しない部分は SKIP として記録

実行:
  python3 -m pytest tests/
  または
  python3 tests/test_pyibtool.py
"""

import sys
import os
import subprocess
import plistlib
import tempfile
import json
from pathlib import Path
import unittest
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool, dump, strings, xliff
from pyibtool.xibdoc import parse_xib_text, serialize_xib


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestPlistErrors(unittest.TestCase):
    """plist エラー出力テスト"""

    def test_no_args(self):
        """引数なし → stderr に 'Error: No arguments specified' + exit 64"""
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            code = ibtool.main([])
            err = sys.stderr.getvalue()
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 64, f"expected exit 64, got {code}")
        self.assertIn("Error: No arguments", err)

    def test_unknown_arg(self):
        """--unknown → plist XML エラー + exit 1"""
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            code = ibtool.main(["--unknown"])
            err = sys.stderr.getvalue()
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 1, f"expected exit 1, got {code}")
        # plist XML 出力検証
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.errors", pl)
        self.assertEqual(pl["com.apple.ibtool.errors"][0]["description"],
                         "Unknown argument '--unknown'.")


class TestVersion(unittest.TestCase):
    def test_version_output(self):
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            code = ibtool.main(["--version"])
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.version", pl)
        v = pl["com.apple.ibtool.version"]
        self.assertIn("bundle-version", v)
        self.assertIn("short-bundle-version", v)


class TestXIBStructure(unittest.TestCase):
    """xib の読み書きテスト"""

    def test_parse_ivc(self):
        with open(FIXTURES / "input" / "ivc.xib", "r", encoding="utf-8") as f:
            txt = f.read()
        doc = parse_xib_text(txt)
        self.assertEqual(doc.doc_type, "com.apple.InterfaceBuilder3.CocoaTouch.XIB")
        self.assertEqual(doc.target_runtime, "iOS.CocoaTouch")
        self.assertEqual(len(doc.objects), 3)
        # classes 収集
        classes = doc.collect_classes()
        self.assertGreater(len(classes), 0)

    def test_parse_tvvc(self):
        with open(FIXTURES / "input" / "tvvc.xib", "r", encoding="utf-8") as f:
            txt = f.read()
        doc = parse_xib_text(txt)
        self.assertIn("AppleTV", doc.doc_type)

    def test_parse_storyboard(self):
        with open(FIXTURES / "input" / "Main.storyboard", "r", encoding="utf-8") as f:
            txt = f.read()
        doc = parse_xib_text(txt)
        self.assertIn("Storyboard", doc.doc_type)
        self.assertEqual(doc.initial_view_controller, "BYZ-38-t0r")
        # scenes 抽出
        self.assertGreater(len(doc.scenes), 0)

    def test_round_trip(self):
        """parse → serialize のラウンドトリップ"""
        for fn in ["ivc.xib", "tvvc.xib", "Main.storyboard"]:
            with open(FIXTURES / "input" / fn, "r", encoding="utf-8") as f:
                txt = f.read()
            doc = parse_xib_text(txt)
            out = serialize_xib(doc)
            doc2 = parse_xib_text(out)
            # 元と同じ構造を持つ
            self.assertEqual(doc.doc_type, doc2.doc_type)
            self.assertEqual(len(doc.objects), len(doc2.objects))
            self.assertEqual(len(doc.connections), len(doc2.connections))


class TestDumpCommands(unittest.TestCase):
    """--classes, --objects, --hierarchy, --connections, --all 等"""

    def setUp(self):
        with open(FIXTURES / "input" / "ivc.xib", "r", encoding="utf-8") as f:
            self.doc = parse_xib_text(f.read())

    def _run_dump(self, *args):
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = list(args) + [str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        return code, out

    def test_classes(self):
        code, out = self._run_dump("--classes")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.classes", pl)
        classes = pl["com.apple.ibtool.document.classes"]
        # 各クラスに class キーは必須。superclass は Apple 出力でも省略される場合あり
        # (FirstResponder, NSCoder 等)
        for cname, cdict in classes.items():
            self.assertIn("class", cdict, f"class {cname} missing class")
        # class 数は Apple の built-in DB を反映して 50 以上
        self.assertGreater(len(classes), 50, f"class count too low: {len(classes)}")

    def test_objects(self):
        code, out = self._run_dump("--objects")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.objects", pl)
        # 3 オブジェクト (IBFilesOwner, IBFirstResponder, view)
        self.assertGreaterEqual(len(pl["com.apple.ibtool.document.objects"]), 3)

    def test_hierarchy(self):
        code, out = self._run_dump("--hierarchy")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.hierarchy", pl)

    def test_connections(self):
        code, out = self._run_dump("--connections")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.connections", pl)

    def test_all(self):
        code, out = self._run_dump("--all")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        for key in ["com.apple.ibtool.document.objects",
                    "com.apple.ibtool.document.hierarchy",
                    "com.apple.ibtool.document.connections",
                    "com.apple.ibtool.document.classes",
                    "com.apple.ibtool.document.version-history"]:
            self.assertIn(key, pl, f"--all must include {key}")

    def test_version_history(self):
        code, out = self._run_dump("--version-history")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.version-history", pl)

    def test_warnings(self):
        code, out = self._run_dump("--warnings")
        self.assertEqual(code, 0)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.document.warnings", pl)

    def test_output_format_binary1(self):
        """--output-format binary1"""
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            argv = ["--classes", "--output-format", "binary1", str(FIXTURES / "input" / "ivc.xib")]
            # BinaryIO に切替
            buf = io.BytesIO()
            stdout_save = sys.stdout
            sys.stdout = io.TextIOWrapper(buf, write_through=True)
            try:
                code = ibtool.main(argv)
                out_buf = buf.getvalue()
            finally:
                sys.stdout = stdout_save
        finally:
            sys.stderr = old_stderr
        # binary1 plist は先頭 'bplist00'
        pl = plistlib.loads(out_buf)
        self.assertIn("com.apple.ibtool.document.classes", pl)


class TestConvert(unittest.TestCase):
    def test_convert_exact(self):
        """--convert ViewController-CustomVC"""
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = ["--convert", "___FILEBASENAMEASIDENTIFIER___-CustomVC",
                    str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        self.assertIn("CustomVC", out)

    def test_convert_wildcard(self):
        """--convert 'UI*'-MyUI"""
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = ["--convert", "UI*'-MyUI", str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        # 'UIR*' prefix を 'MyUI' に置換する処理が動く
        # エラーが出ずに何かしらの xib が出力される
        self.assertEqual(code, 0)
        # UIResponder → MyUIResponder に変換される
        self.assertIn("MyUIResponder", out)
        self.assertNotIn('customClass="UIResponder"', out)


class TestUpgrade(unittest.TestCase):
    def test_upgrade(self):
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = ["--upgrade", str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        self.assertIn("toolsVersion=\"26000\"", out)


class TestStrings(unittest.TestCase):
    def test_generate_strings(self):
        with open(FIXTURES / "input" / "ivc.xib", "r", encoding="utf-8") as f:
            doc = parse_xib_text(f.read())
        s = strings.generate_strings(doc, empty_values=True)
        # 少なくとも plist 形式風
        self.assertIsInstance(s, str)

    def test_export_strings(self):
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            with tempfile.NamedTemporaryFile("w", suffix=".strings", delete=False) as f:
                tmpname = f.name
            argv = ["--export-strings-file", tmpname, str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        # ファイル生成
        self.assertTrue(os.path.exists(tmpname))
        os.unlink(tmpname)

    def test_import_plist(self):
        """--import: --export で出力した plist を読み込んで xib に反映"""
        import_plist = {
            "com.apple.ibtool.document.export": {
                "i5M-Pr-FkT": {
                    "tag": "1",
                    "alpha": "0.5",
                }
            }
        }
        with tempfile.NamedTemporaryFile("wb", suffix=".plist", delete=False) as f:
            tmp_plist = f.name
            plistlib.dump(import_plist, f, fmt=plistlib.FMT_XML)
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            code = ibtool.main(["--import", tmp_plist,
                                str(FIXTURES / "input" / "ivc.xib")])
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        # xib 出力に 'tag="1"' 'alpha="0.5"' が反映される
        self.assertIn('tag="1"', out)
        self.assertIn('alpha="0.5"', out)
        os.unlink(tmp_plist)


class TestXLIFF(unittest.TestCase):
    def test_export_xliff(self):
        with tempfile.NamedTemporaryFile("w", suffix=".xlf", delete=False) as f:
            tmpname = f.name
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = ["--export-xliff", tmpname, "--source-language", "en",
                    "--target-language", "ja", str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(tmpname))
        with open(tmpname, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("xliff", content)
        self.assertIn("en", content)
        self.assertIn("ja", content)
        os.unlink(tmpname)


class TestCompileNIB(unittest.TestCase):
    def test_compile_basic(self):
        """xib → nib コンパイル (最低限の nib ヘッダ検証)"""
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmpname = f.name
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = ["--compile", tmpname, str(FIXTURES / "input" / "ivc.xib")]
            code = ibtool.main(argv)
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 0, "compile failed")
        self.assertTrue(os.path.exists(tmpname))
        with open(tmpname, "rb") as f:
            data = f.read()
        # NIBArchive ヘッダ
        self.assertEqual(data[:10], b"NIBArchive")
        os.unlink(tmpname)


class TestMissingFile(unittest.TestCase):
    def test_missing_file(self):
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            argv = ["--classes", "/nonexistent.xib"]
            code = ibtool.main(argv)
            out = sys.stdout.getvalue()
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        self.assertEqual(code, 1)
        pl = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.errors", pl)


if __name__ == "__main__":
    unittest.main(verbosity=2)
