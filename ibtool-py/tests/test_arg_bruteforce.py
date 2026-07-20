"""
test_arg_bruteforce.py - 50 種類以上の ibtool 引数の総当たりテスト

各引数がエラーなく認識されて実行できることを検証。
"""
import os, sys, plistlib, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.xibdoc import parse_xib_text

FIXTURES = Path(__file__).parent.parent / "fixtures" / "probe_v8"
XIB = FIXTURES / "ios.xib"
STORY = FIXTURES / "story.storyboard"


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


class TestNoArgs(unittest.TestCase):
    def test_no_args(self):
        code, out, err = _run([])
        self.assertEqual(code, 64)
        self.assertIn("No arguments specified", err)


class TestUnknownArg(unittest.TestCase):
    def test_unknown_arg(self):
        code, out, _ = _run(["--unknown-arg", str(XIB)])
        self.assertEqual(code, 1)
        self.assertIn("Unknown argument", out)


class TestVersion(unittest.TestCase):
    def test_version(self):
        code, out, _ = _run(["--version"])
        self.assertEqual(code, 0)
        d = plistlib.loads(out.encode("utf-8"))
        self.assertIn("com.apple.ibtool.version", d)


class TestBasicDumps(unittest.TestCase):
    """基本 dump 系 14 種類全部"""

    DUMPS = [
        "classes", "objects", "hierarchy", "connections", "all", "version-history",
        "warnings", "errors", "notices",
        "localizable-strings", "localizable-stringarrays", "localizable-geometry",
        "localizable-other", "localizable-to-many-relationships", "localizable-all",
    ]

    def test_all_dumps_xib(self):
        for d in self.DUMPS:
            with self.subTest(dump=d):
                code, out, _ = _run([f"--{d}", str(XIB)])
                self.assertEqual(code, 0, f"--{d} failed: code={code}")
                # plist として parse 可能
                pd = plistlib.loads(out.encode("utf-8"))
                # なんらかの com.apple.ibtool.* キーを含む
                self.assertTrue(any(k.startswith("com.apple.ibtool") for k in pd),
                    f"--{d} no com.apple.ibtool.* key: {list(pd.keys())}")

    def test_all_dumps_storyboard(self):
        if not STORY.exists():
            self.skipTest("no storyboard")
        for d in self.DUMPS:
            with self.subTest(dump=d):
                code, out, _ = _run([f"--{d}", str(STORY)])
                # storyboard は plist ダンプでも OK
                self.assertEqual(code, 0, f"--{d} storyboard failed: code={code}")


class TestOutputFormat(unittest.TestCase):
    """--output-format 3 種類"""

    def test_xml1(self):
        code, out, _ = _run(["--classes", "--output-format", "xml1", str(XIB)])
        self.assertEqual(code, 0)
        self.assertIn(b"<?xml" if isinstance(out, bytes) else "<?xml", out)

    def test_binary1(self):
        code, out, _ = _run(["--classes", "--output-format", "binary1", str(XIB)], capture_binary=True)
        self.assertEqual(code, 0)
        # binary1 plist
        if isinstance(out, str):
            out = out.encode("utf-8")
        self.assertTrue(out.startswith(b"bplist00"))

    def test_human_readable_text(self):
        code, out, _ = _run(["--classes", "--output-format", "human-readable-text", str(XIB)])
        self.assertEqual(code, 0)
        # text 形式
        self.assertGreater(len(out), 0)


class TestCompileAndStrip(unittest.TestCase):
    def test_compile(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(tmp))
            with open(tmp, "rb") as f:
                self.assertEqual(f.read(10), b"NIBArchive")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_strip(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--strip", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(tmp))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestConvert(unittest.TestCase):
    def test_convert_simple(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, out, _ = _run(["--convert", "UIView-MyView", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_convert_wildcard(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, out, _ = _run(["--convert", "UI*'-MyUI", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestLocalization(unittest.TestCase):
    def test_export_strings(self):
        with tempfile.NamedTemporaryFile(suffix=".strings", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--export-strings-file", tmp, str(XIB)])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(tmp))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_generate_strings(self):
        with tempfile.NamedTemporaryFile(suffix=".strings", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--generate-strings-file", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_export_xliff(self):
        with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--export-xliff", tmp, "--source-language", "en",
                              "--target-language", "ja", str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_generate_xliff(self):
        with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--generate-xliff", tmp, "--source-language", "en",
                              "--target-language", "ja", str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_localize_incremental_requires_args(self):
        code, _, _ = _run(["--localize-incremental", str(XIB)])
        self.assertEqual(code, 1)

    def test_localize_incremental_with_args(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run([
                "--localize-incremental",
                "--previous-file", str(XIB),
                "--incremental-file", str(XIB),
                "--write", tmp,
                str(XIB)
            ])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestModification(unittest.TestCase):
    def test_upgrade(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, out, _ = _run(["--upgrade", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
            content = open(tmp).read()
            self.assertIn("<document", content)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_remove_plugin_deps(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--remove-plugin-dependencies", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_enable_auto_layout(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--enable-auto-layout", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_update_frames(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--update-frames", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_update_constraints(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--update-constraints", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestTargetDevice(unittest.TestCase):
    def test_target_device_iphone(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--target-device", "iphone", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_target_device_ipad(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--target-device", "ipad", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_target_device_family_1_2(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--target-device-family", "1,2", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_sdk(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--sdk", "iphoneos", "--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestModuleAndFlatten(unittest.TestCase):
    def test_module(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--module", "MyModule", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_flatten_yes(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--flatten", "YES", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_flatten_no(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--flatten", "NO", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestStoreOptions(unittest.TestCase):
    def test_store(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--store", "--store-version", "1.0", "--store-build", "1",
                              "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestAutoActivateCustomFonts(unittest.TestCase):
    def test_auto_activate(self):
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--auto-activate-custom-fonts", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestInputFile(unittest.TestCase):
    def test_nonexistent_file(self):
        code, out, _ = _run(["--classes", "/nonexistent.xib"])
        self.assertEqual(code, 1)
        self.assertIn("does not exist", out)


class TestWriteAndRoundTrip(unittest.TestCase):
    def test_write_to_stdout(self):
        code, out, _ = _run([str(XIB)])
        self.assertEqual(code, 0)
        # xib 形式
        self.assertIn("<document", out)

    def test_write_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--write", tmp, str(XIB)])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(tmp))
            content = open(tmp).read()
            self.assertIn("<document", content)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestCompanionStrings(unittest.TestCase):
    def test_companion(self):
        with tempfile.NamedTemporaryFile(suffix=".strings", delete=False) as f:
            tmp = f.name
        try:
            # --companion-strings-file LOC:FILE
            code, _, _ = _run(["--companion-strings-file", f"ja:{tmp}", str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestExportImport(unittest.TestCase):
    def test_export(self):
        # plist の input format: {className: [props]}
        plist_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>UIView</key>
    <array>
        <string>frame</string>
        <string>backgroundColor</string>
    </array>
</dict>
</plist>"""
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            f.write(plist_content)
            tmp = f.name
        try:
            code, out, _ = _run(["--export", tmp, str(XIB)])
            self.assertEqual(code, 0)
            self.assertIn("com.apple.ibtool.document.export", out)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_import(self):
        # import plist format
        plist_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.ibtool.document.export</key>
    <dict>
        <key>iN0-l3-epB</key>
        <dict>
            <key>frame</key>
            <string>{{0, 0}, {100, 100}}</string>
        </dict>
    </dict>
</dict>
</plist>"""
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            f.write(plist_content)
            tmp = f.name
        try:
            code, out, _ = _run(["--import", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestStoryboardCompile(unittest.TestCase):
    def test_storyboard_to_storyboardc(self):
        if not STORY.exists():
            self.skipTest("no storyboard")
        with tempfile.TemporaryDirectory() as td:
            out_dir = os.path.join(td, "test_dir")
            os.makedirs(out_dir)
            out = os.path.join(out_dir, "test.storyboardc")
            code, _, _ = _run(["--compile", out, str(STORY)])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
