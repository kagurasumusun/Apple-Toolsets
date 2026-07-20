"""
test_man_page_examples.py - Apple ibtool man ページの EXAMPLES を完全再現

man ページ (Aug 15 2008) の EXAMPLES セクション:
  ibtool --export-strings-file file.strings file.nib
  ibtool --previous-file orig.nib --incremental-file trans.nib --localize-incremental --write newTrans.nib mod.nib
  ibtool --warnings --errors --notices file.nib > alerts.plist
  ibtool --plugin path/to/some.plugin --localizable-geometry file.nib
  ibtool --convert oldName-newName file.nib
  ibtool --convert Old'*'-New file
  ibtool --export export.plist file.nib
  ibtool --export-xliff generated.xlf inputDocument.xib
  ibtool --export-xliff generated.xlf --source-language es --target-language fr inputDocument.xib
  ibtool --import-xliff translation.xlf --write translated.xib inputDocument.xib
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


class TestManPageExampleExportStrings(unittest.TestCase):
    def test_export_strings(self):
        """ibtool --export-strings-file file.strings file.nib"""
        with tempfile.NamedTemporaryFile(suffix=".strings", delete=False) as f:
            tmp = f.name
        try:
            code, _, _ = _run(["--export-strings-file", tmp, str(XIB)])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(tmp))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestManPageExampleLocalizeIncremental(unittest.TestCase):
    def test_localize_incremental(self):
        """ibtool --previous-file orig.nib --incremental-file trans.nib --localize-incremental --write newTrans.nib mod.nib"""
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            new_xib = f.name
        try:
            code, _, _ = _run([
                "--previous-file", str(XIB),
                "--incremental-file", str(XIB),
                "--localize-incremental",
                "--write", new_xib,
                str(XIB)
            ])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(new_xib))
        finally:
            if os.path.exists(new_xib):
                os.unlink(new_xib)


class TestManPageExampleWarningsErrorsNotices(unittest.TestCase):
    def test_warnings_errors_notices(self):
        """ibtool --warnings --errors --notices file.nib > alerts.plist"""
        code, out, _ = _run(["--warnings", "--errors", "--notices", str(XIB)])
        self.assertEqual(code, 0)
        d = plistlib.loads(out.encode("utf-8"))
        # 3 つのキー全部
        self.assertIn("com.apple.ibtool.document.warnings", d)
        self.assertIn("com.apple.ibtool.document.errors", d)
        self.assertIn("com.apple.ibtool.document.notices", d)


class TestManPageExamplePlugin(unittest.TestCase):
    def test_plugin(self):
        """ibtool --plugin path/to/some.plugin --localizable-geometry file.nib"""
        # /nonexistent パスでも unknown ではないことを確認
        code, out, _ = _run(["--plugin", "/nonexistent.plugin", "--localizable-geometry", str(XIB)])
        # error かもしれないが Unknown argument ではない
        self.assertNotIn("Unknown argument '--plugin'", out)
        self.assertNotIn("Unknown argument '--localizable-geometry'", out)


class TestManPageExampleConvert(unittest.TestCase):
    def test_convert_simple(self):
        """ibtool --convert oldName-newName file.nib"""
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            out_xib = f.name
        try:
            code, _, _ = _run(["--convert", "UIView-MyView", "--write", out_xib, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(out_xib):
                os.unlink(out_xib)

    def test_convert_wildcard(self):
        """ibtool --convert Old'*'-New file"""
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            out_xib = f.name
        try:
            code, _, _ = _run(["--convert", "UI*'-MyUI", "--write", out_xib, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(out_xib):
                os.unlink(out_xib)


class TestManPageExampleExport(unittest.TestCase):
    def test_export(self):
        """ibtool --export export.plist file.nib"""
        # サンプル plist: NSCell title
        plist_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>UIView</key>
<array><string>contentMode</string></array>
</dict></plist>"""
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            f.write(plist_content)
            plist = f.name
        try:
            code, out, _ = _run(["--export", plist, str(XIB)])
            self.assertEqual(code, 0)
            d = plistlib.loads(out.encode("utf-8"))
            self.assertIn("com.apple.ibtool.document.export", d)
        finally:
            if os.path.exists(plist):
                os.unlink(plist)


class TestManPageExampleExportXliff(unittest.TestCase):
    def test_export_xliff_no_lang(self):
        """ibtool --export-xliff generated.xlf inputDocument.xib"""
        with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as f:
            xlf = f.name
        try:
            code, _, _ = _run(["--export-xliff", xlf, str(XIB)])
            self.assertEqual(code, 0)
            with open(xlf) as f: content = f.read()
            self.assertIn("xliff", content)
        finally:
            if os.path.exists(xlf):
                os.unlink(xlf)

    def test_export_xliff_with_lang(self):
        """ibtool --export-xliff generated.xlf --source-language es --target-language fr inputDocument.xib"""
        with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False) as f:
            xlf = f.name
        try:
            code, _, _ = _run(["--export-xliff", xlf,
                              "--source-language", "es",
                              "--target-language", "fr", str(XIB)])
            self.assertEqual(code, 0)
            with open(xlf) as f: content = f.read()
            self.assertIn('source-language="es"', content)
            self.assertIn('target-language="fr"', content)
        finally:
            if os.path.exists(xlf):
                os.unlink(xlf)


class TestManPageExampleImportXliff(unittest.TestCase):
    def test_import_xliff(self):
        """ibtool --import-xliff translation.xlf --write translated.xib inputDocument.xib"""
        xlf_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:ib="com.apple.InterfaceBuilder3" version="1.2">
<file original="ios.xib" datatype="x-ib">
<body><group ib:member-type="objects"></group></body>
</file>
</xliff>'''
        with tempfile.NamedTemporaryFile(suffix=".xlf", delete=False, mode='w') as f:
            f.write(xlf_content)
            xlf = f.name
        with tempfile.NamedTemporaryFile(suffix=".xib", delete=False) as f:
            translated = f.name
        try:
            code, _, _ = _run(["--import-xliff", xlf, "--write", translated, str(XIB)])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(translated))
        finally:
            for p in [xlf, translated]:
                if os.path.exists(p):
                    os.unlink(p)


class TestManPageExampleAgent(unittest.TestCase):
    def test_agent_name_recognized(self):
        """--agent-name NAME が認識される (man example: ibtool --agent-name CMPAgent --all file.nib)"""
        code, out, _ = _run(["--agent-name", "CMPAgent", "--all", str(XIB)])
        # ok or error だが Unknown argument ではない
        self.assertNotIn("Unknown argument '--agent-name'", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
