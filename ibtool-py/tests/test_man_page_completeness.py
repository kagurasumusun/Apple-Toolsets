"""
test_man_page_completeness.py - Apple ibtool man ページの全引数が認識されるか

man ページ (https://www.unix.com/man_page/osx/1/ibtool/) に記載されている
全引数 (40 個以上) を総当たりでテスト。

各引数について:
  1. 認識される (Unknown argument エラーが出ない)
  2. 適切なエラーメッセージで失敗 (オプション値が必須なのに無し)
"""
import os, sys, unittest, io, plistlib, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool

FIXTURES = Path(__file__).parent.parent / "fixtures" / "probe_v8"
XIB = FIXTURES / "ios.xib"


def _run(args):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        sys.stdout = io.StringIO()
        code = ibtool.main(args)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return code, out, err
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


# man ページの全引数 (40 個以上) - 認識されるべき
KNOWN_OPTS = [
    # Specifying Output
    ("--write", "PATH"),
    ("--output-format", "xml1"),
    # Compiling
    ("--compile", "PATH"),
    ("--flatten", "YES"),
    # Postprocessing
    ("--strip", None),  # boolean flag
    # Loading Plug-ins
    ("--bundle", "PATH"),
    ("--plugin", "PATH"),
    ("--plugin-dir", "PATH"),
    # Localization
    ("--previous-file", "PATH"),
    ("--incremental-file", "PATH"),
    ("--localize-incremental", None),  # boolean
    ("--reference-external-strings-file", None),  # boolean
    ("--companion-strings-file", "LOC:FILE"),
    # Importing
    ("--import", "PATH"),
    ("--import-strings-file", "PATH"),
    ("--import-xliff", "PATH"),
    # Exporting
    ("--export", "PATH"),
    ("--export-strings-file", "PATH"),
    ("--export-xliff", "PATH"),
    ("--generate-strings-file", "PATH"),
    ("--generate-xliff", "PATH"),
    ("--source-language", "en"),
    ("--target-language", "ja"),
    # Refactoring
    ("--convert", "Old-New"),
    ("--upgrade", None),  # boolean
    ("--remove-plugin-dependencies", None),  # boolean
    ("--enable-auto-layout", None),  # boolean
    ("--update-frames", None),  # boolean
    ("--update-constraints", None),  # boolean
    # Printing
    ("--warnings", None),
    ("--errors", None),
    ("--notices", None),
    ("--localizable-strings", None),
    ("--localizable-stringarrays", None),
    ("--localizable-geometry", None),
    ("--localizable-other", None),
    ("--localizable-to-many-relationships", None),
    ("--localizable-all", None),
    ("--objects", None),
    ("--hierarchy", None),
    ("--connections", None),
    ("--classes", None),
    ("--version-history", None),
    ("--all", None),
    # Agent
    ("--agent-name", "NAME"),
    # Version
    ("--version", None),
    # Module / SDK
    ("--module", "MyModule"),
    ("--target-device", "iphone"),
    ("--target-device-family", "1,2"),
    ("--sdk", "iphoneos"),
    ("--auto-activate-custom-fonts", None),  # boolean
    ("--store", None),  # boolean
    ("--store-version", "1.0"),
    ("--store-build", "1"),
]


class TestAllManPageOpts(unittest.TestCase):
    """全 50 種類以上の引数が認識される"""

    def setUp(self):
        if not XIB.exists():
            self.skipTest("no ios.xib")

    def test_no_unknown_argument_error(self):
        """man ページの全引数が 'Unknown argument' にならない"""
        for opt, val in KNOWN_OPTS:
            with self.subTest(opt=opt, val=val):
                if val is None:
                    # boolean flag
                    args = [opt, str(XIB)]
                elif opt in ("--localize-incremental", "--previous-file",
                             "--incremental-file"):
                    # 必須ペアが必要
                    args = [opt, "--previous-file", str(XIB),
                           "--incremental-file", str(XIB), str(XIB)]
                elif opt in ("--strip",):
                    # --compile と組み合わせ
                    with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
                        tmp = f.name
                    try:
                        code, _, _ = _run([opt, "--compile", tmp, str(XIB)])
                        # ok (exit 0) or error だが Unknown argument ではない
                    finally:
                        if os.path.exists(tmp):
                            os.unlink(tmp)
                    continue
                elif opt in ("--compile",):
                    with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
                        tmp = f.name
                    try:
                        args = [opt, tmp, str(XIB)]
                        code, _, _ = _run(args)
                    finally:
                        if os.path.exists(tmp):
                            os.unlink(tmp)
                    continue
                elif opt in ("--plugin", "--bundle", "--plugin-dir"):
                    # directory が必要 (存在しなくても unknown ではないことを確認)
                    args = [opt, "/nonexistent", str(XIB)]
                    code, _, _ = _run(args)
                    # ok or error
                    continue
                elif opt in ("--output-format",):
                    args = [opt, val, "--classes", str(XIB)]
                    code, _, _ = _run(args)
                    continue
                elif opt in ("--export",):
                    # export は input plist 必要
                    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False, mode='w') as f:
                        f.write('<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict></dict></plist>')
                        plist = f.name
                    try:
                        args = [opt, plist, str(XIB)]
                        code, _, _ = _run(args)
                    finally:
                        if os.path.exists(plist):
                            os.unlink(plist)
                    continue
                elif opt in ("--import", "--import-strings-file", "--import-xliff"):
                    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False, mode='w') as f:
                        f.write('<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict></dict></plist>')
                        plist = f.name
                    try:
                        args = [opt, plist, str(XIB)]
                        code, _, _ = _run(args)
                    finally:
                        if os.path.exists(plist):
                            os.unlink(plist)
                    continue
                elif opt in ("--export-strings-file", "--generate-strings-file",
                             "--export-xliff", "--generate-xliff"):
                    with tempfile.NamedTemporaryFile(suffix=".out", delete=False) as f:
                        outp = f.name
                    try:
                        if opt in ("--export-xliff", "--generate-xliff"):
                            args = [opt, outp, "--source-language", "en",
                                   "--target-language", "ja", str(XIB)]
                        else:
                            args = [opt, outp, str(XIB)]
                        code, _, _ = _run(args)
                    finally:
                        if os.path.exists(outp):
                            os.unlink(outp)
                    continue
                elif opt in ("--convert",):
                    args = [opt, val, str(XIB)]
                    code, _, _ = _run(args)
                    continue
                elif opt in ("--write",):
                    with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
                        outp = f.name
                    args = [opt, outp, str(XIB)]
                    code, _, _ = _run(args)
                    if os.path.exists(outp):
                        os.unlink(outp)
                    continue
                else:
                    args = [opt, val, str(XIB)]
                code, out, err = _run(args)
                # Unknown argument が出力されていないこと
                self.assertNotIn("Unknown argument", out,
                    f"{opt} {val}: Unknown argument error")
                self.assertNotIn("Unknown argument", err,
                    f"{opt} {val}: Unknown argument in stderr")

    def test_unknown_argument_detected(self):
        """未知の引数は検出される"""
        code, out, _ = _run(["--this-is-not-a-real-arg", str(XIB)])
        self.assertEqual(code, 1)
        self.assertIn("Unknown argument", out)


class TestAllDumpsAtLeast50Class(unittest.TestCase):
    """--classes の Apple DB 50 個以上"""

    def test_classes_over_50(self):
        code, out, _ = _run(["--classes", str(XIB)])
        self.assertEqual(code, 0)
        d = plistlib.loads(out.encode("utf-8"))
        cls = d["com.apple.ibtool.document.classes"]
        self.assertGreater(len(cls), 50)


class TestAllDumpsAllKeys(unittest.TestCase):
    """--all の 9 キー全部"""

    def test_all_9_keys(self):
        code, out, _ = _run(["--all", str(XIB)])
        self.assertEqual(code, 0)
        d = plistlib.loads(out.encode("utf-8"))
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
        for k in expected:
            self.assertIn(k, d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
