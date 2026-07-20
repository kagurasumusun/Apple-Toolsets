"""
test_extended_opts.py - Apple ibtool の拡張・隠し引数の認識確認

man ページに明記されていない、Apple 内部ビルドツールでも使われる拡張引数。
SDK 不要の portable 実装で全て認識されることを確認。
"""
import os, sys, unittest, io
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
        return code, out
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


class TestExtendedOpts(unittest.TestCase):
    def setUp(self):
        if not XIB.exists():
            self.skipTest("no xib fixture")

    def test_minimum_deployment_target(self):
        code, out = _run(["--minimum-deployment-target", "13.0", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_deployment_target(self):
        code, out = _run(["--deployment-target", "14.0", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_pipeline(self):
        code, out = _run(["--no-pipeline", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_warnings(self):
        code, out = _run(["--no-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_print_errors(self):
        code, out = _run(["--print-errors", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_output_encoding(self):
        code, out = _run(["--output-encoding", "utf-8", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_validation(self):
        for v in ["strict", "lenient", "minimal"]:
            code, out = _run(["--validation", v, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_no_flatten(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _ = _run(["--no-flatten", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_stack_trace(self):
        code, out = _run(["--stack-trace", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_verbose(self):
        code, out = _run(["--verbose", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_quiet(self):
        code, out = _run(["--quiet", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_localization(self):
        code, out = _run(["--localization", "ja", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_language(self):
        code, out = _run(["--language", "en", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_locales(self):
        for locales in ["en,ja", "en,ja,fr,de", "*"]:
            code, out = _run(["--locales", locales, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_resource_rules(self):
        code, out = _run(["--resource-rules", "/tmp/rr.plist", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_thinning(self):
        for arch in ["arm64", "armv7", "x86_64", "i386"]:
            code, out = _run(["--thinning", arch, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_flatten_recursively(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
            tmp = f.name
        try:
            code, _ = _run(["--flatten-recursively", "--compile", tmp, str(XIB)])
            self.assertEqual(code, 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_serialize(self):
        code, out = _run(["--serialize", "/tmp/ser.xib", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_relax_link_validation(self):
        code, out = _run(["--no-relax-link-validation", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_relax_link_validation(self):
        code, out = _run(["--relax-link-validation", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_pretty(self):
        code, out = _run(["--pretty", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_validate(self):
        code, out = _run(["--validate", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_verify(self):
        code, out = _run(["--verify", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_cache(self):
        code, out = _run(["--cache", "/tmp/ibtool_cache", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_cache(self):
        code, out = _run(["--no-cache", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_primary_language(self):
        code, out = _run(["--primary-language", "en", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_development_language(self):
        code, out = _run(["--development-language", "en", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_known_regions(self):
        code, out = _run(["--known-regions", "en,ja,fr,de", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_fallback_language(self):
        code, out = _run(["--fallback-language", "en", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_default_language(self):
        code, out = _run(["--default-language", "en", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_include_storyboards(self):
        code, out = _run(["--include-storyboards", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_include_storyboards(self):
        code, out = _run(["--no-include-storyboards", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_intents(self):
        code, out = _run(["--intents", "/tmp/intents.xml", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_intents(self):
        code, out = _run(["--no-intents", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_ibwarnings(self):
        code, out = _run(["--ibwarnings", "/tmp/w.plist", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_ibnotices(self):
        code, out = _run(["--ibnotices", "/tmp/n.plist", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_module_warnings(self):
        code, out = _run(["--no-module-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_output_path(self):
        code, out = _run(["--output-path", "/tmp/out", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_ignore_missing_modules(self):
        code, out = _run(["--ignore-missing-modules", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_module_path(self):
        code, out = _run(["--module-path", "/tmp/modules", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_headers_path(self):
        code, out = _run(["--headers-path", "/tmp/headers", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_frameworks_path(self):
        code, out = _run(["--frameworks-path", "/tmp/frameworks", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_sdk_path(self):
        code, out = _run(["--sdk-path", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_toolchain(self):
        code, out = _run(["--toolchain", "Xcode", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_platform_name(self):
        code, out = _run(["--platform-name", "iPhoneOS", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_platform_path(self):
        code, out = _run(["--platform-path", "/tmp/platform", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_print_warnings(self):
        code, out = _run(["--print-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_sdkroot(self):
        code, out = _run(["--sdkroot", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_target(self):
        for t in ["arm64-apple-ios13.0", "x86_64-apple-ios14.0-simulator", "arm64-apple-macos11.0"]:
            code, out = _run(["--target", t, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_allow_objc_modules(self):
        code, out = _run(["--allow-obj-c-modules", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_allow_objc_modules(self):
        code, out = _run(["--no-allow-obj-c-modules", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_enable_objc_modules(self):
        code, out = _run(["--enable-obj-c-modules", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_disable_objc_modules(self):
        code, out = _run(["--disable-obj-c-modules", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_runtime_args(self):
        code, out = _run(["--runtime-args", "arg1", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_dependency_info(self):
        code, out = _run(["--dependency-info", "/tmp/d", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_emit_dependency_info(self):
        code, out = _run(["--emit-dependency-info", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_emit_dependency_info(self):
        code, out = _run(["--no-emit-dependency-info", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_product_type(self):
        code, out = _run(["--product-type", "com.apple.product-type.app", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_track_changes(self):
        code, out = _run(["--track-changes", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_track_changes(self):
        code, out = _run(["--no-track-changes", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_ib_class_info(self):
        code, out = _run(["--ib-class-info", "/tmp/ib.json", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_emit_ib_class_info(self):
        code, out = _run(["--emit-ib-class-info", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_doc(self):
        code, out = _run(["--doc", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_docs(self):
        code, out = _run(["--docs", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_detailed_warnings(self):
        code, out = _run(["--detailed-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_detailed_warnings(self):
        code, out = _run(["--no-detailed-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_print_deprecation_warnings(self):
        code, out = _run(["--print-deprecation-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_print_deprecation_warnings(self):
        code, out = _run(["--no-print-deprecation-warnings", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_strict(self):
        code, out = _run(["--strict", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_strict(self):
        code, out = _run(["--no-strict", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_region(self):
        for r in ["en", "ja", "Base"]:
            code, out = _run(["--region", r, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_regions(self):
        code, out = _run(["--regions", "en,ja,Base", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_input_format(self):
        code, out = _run(["--input-format", "xib", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_output_format_options(self):
        code, out = _run(["--output-format-options", "compact", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_load_plugin(self):
        code, out = _run(["--load-plugin", "/tmp/p", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_arch(self):
        for a in ["arm64", "x86_64", "i386", "armv7"]:
            code, out = _run(["--arch", a, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_universal(self):
        code, out = _run(["--universal", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_no_universal(self):
        code, out = _run(["--no-universal", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_platform(self):
        for p in ["iPhoneOS", "iPhoneSimulator", "AppleTVOS", "macOSX", "WatchOS"]:
            code, out = _run(["--platform", p, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)

    def test_build(self):
        code, out = _run(["--build", "18A1", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_deployment_os(self):
        code, out = _run(["--deployment-os", "iOS 13.0", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_minimum_os(self):
        code, out = _run(["--minimum-os", "iOS 13.0", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_target_os(self):
        code, out = _run(["--target-os", "iOS 14.0", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_device_arg(self):
        code, out = _run(["--device", "iPhone", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_os_version(self):
        code, out = _run(["--os-version", "13.0", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_xros(self):
        code, out = _run(["--xros", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_tvos(self):
        code, out = _run(["--tvos", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_watchos(self):
        code, out = _run(["--watchos", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_ios(self):
        code, out = _run(["--ios", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_macos(self):
        code, out = _run(["--macos", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_visionos(self):
        code, out = _run(["--visionos", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_catalyst(self):
        code, out = _run(["--catalyst", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_appletvos(self):
        code, out = _run(["--appletvos", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_bridgeos(self):
        code, out = _run(["--bridgeos", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_driverkit(self):
        code, out = _run(["--driverkit", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_xrsdk(self):
        code, out = _run(["--xrsdk", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_iphonesimulatorsdk(self):
        code, out = _run(["--iphonesimulatorsdk", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_appletvsimulatorsdk(self):
        code, out = _run(["--appletvsimulatorsdk", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_watchsimulatorsdk(self):
        code, out = _run(["--watchsimulatorsdk", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_xrsimulatorsdk(self):
        code, out = _run(["--xrsimulatorsdk", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_macosx_sdk(self):
        code, out = _run(["--macosx-sdk", "/tmp/sdk", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_embedded(self):
        code, out = _run(["--embedded", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_simulator(self):
        code, out = _run(["--simulator", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)

    def test_device_family(self):
        code, out = _run(["--device-family", "iPhone,iPad", "--classes", str(XIB)])
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown argument", out)


class TestTargetDevicesAll(unittest.TestCase):
    """--target-device の全 Apple 値"""

    def test_all_devices(self):
        for dev in ["iphone", "ipad", "appletv", "watch", "xr", "mac", "car",
                    "iPhone", "iPad", "iPhone6,1"]:
            code, out = _run(["--target-device", dev, "--classes", str(XIB)])
            self.assertEqual(code, 0)
            self.assertNotIn("Unknown argument", out)


class TestSDKDontNeed(unittest.TestCase):
    """pyibtool は SDK 不要で Apple 系全 xib を compile 可能"""

    def setUp(self):
        self.candidates = []
        for f in ["ios.xib", "tvos.xib", "watch.xib", "xr.xib", "story.storyboard"]:
            p = FIXTURES / f
            if p.exists():
                self.candidates.append(p)
        if not self.candidates:
            self.skipTest("no fixtures")

    def test_compile_without_sdk(self):
        """SDK なしで全 platform xib compile"""
        import tempfile
        for xib in self.candidates:
            with self.subTest(file=xib.name):
                out_ext = ".storyboardc" if "storyboard" in xib.name else ".nib"
                with tempfile.TemporaryDirectory() as td:
                    if out_ext == ".storyboardc":
                        tmp = os.path.join(td, xib.stem + ".storyboardc")
                    else:
                        with tempfile.NamedTemporaryFile(suffix=".nib", delete=False) as f:
                            tmp = f.name
                    try:
                        code, _ = _run(["--compile", tmp, str(xib)])
                        self.assertEqual(code, 0, f"compile failed for {xib.name}")
                        if out_ext == ".nib":
                            self.assertGreater(os.path.getsize(tmp), 0)
                        else:
                            self.assertTrue(os.path.isdir(tmp))
                    finally:
                        if os.path.exists(tmp) and not os.path.isdir(tmp):
                            os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
