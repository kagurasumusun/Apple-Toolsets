"""
test_viraptor_full_compile.py - viraptor/ibtool の全 xib (164 個) を pyibtool で compile
"""
import os, sys, unittest, io, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pyibtool import ibtool
from pyibtool.nibarchive import parse_nib

VIRAPTOR_XIB = Path(__file__).parent.parent / "fixtures" / "viraptor_xib"


def _run(args):
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    try:
        sys.stderr = io.StringIO()
        sys.stdout = io.BytesIO()
        code = ibtool.main(args)
        return code
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestAllViraptorXibCompile(unittest.TestCase):
    def setUp(self):
        if not VIRAPTOR_XIB.exists():
            self.skipTest("no viraptor xib fixtures")
        self.files = sorted(VIRAPTOR_XIB.glob("*.xib"))
        if not self.files:
            self.skipTest("no xib files")

    def test_compile_all_xib(self):
        """全 xib → pyibtool --compile"""
        ok = 0
        err = 0
        for f in self.files:
            with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as t:
                tmp = t.name
            try:
                code = _run(["--compile", tmp, str(f)])
                if code == 0 and os.path.exists(tmp):
                    ok += 1
                else:
                    err += 1
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        print(f"  compile: {ok}/{len(self.files)} ok, {err} err")
        self.assertEqual(err, 0, f"{err} compile failures")
        self.assertEqual(ok, len(self.files), f"only {ok}/{len(self.files)} compiled")

    def test_compile_output_parseable_by_pyibtool(self):
        """全 compile 出力を pyibtool parse_nib で読める"""
        ok = 0
        for f in self.files:
            with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as t:
                tmp = t.name
            try:
                code = _run(["--compile", tmp, str(f)])
                if code == 0:
                    with open(tmp, "rb") as fp:
                        try:
                            arch = parse_nib(fp.read())
                            if arch.class_names:
                                ok += 1
                        except Exception:
                            pass
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        print(f"  parseable: {ok}/{len(self.files)}")
        self.assertEqual(ok, len(self.files))


if __name__ == "__main__":
    unittest.main(verbosity=2)
