from __future__ import annotations

import argparse
from pathlib import Path
import sys
import json

from .compiler import CompileOptions, compile_catalogs

VERSION = "actool-linux 0.1.0 (clean-room compatibility layer)"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="actool", allow_abbrev=False)
    p.add_argument("inputs", nargs="*", type=Path)
    p.add_argument("--compile", dest="output", type=Path)
    p.add_argument("--platform")
    p.add_argument("--minimum-deployment-target")
    p.add_argument("--app-icon")
    p.add_argument("--accent-color")
    p.add_argument("--launch-image")
    p.add_argument("--output-partial-info-plist", type=Path)
    p.add_argument("--warnings", choices=("yes", "no"), default="yes")
    p.add_argument("--errors", choices=("yes", "no"), default="yes")
    p.add_argument("--notices", choices=("yes", "no"), default="yes")
    p.add_argument("--target-device", action="append", choices=("iphone","ipad","tv","watch","mac","vision"), default=[])
    p.add_argument("--filter-for-device-model")
    p.add_argument("--filter-for-device-os-version")
    p.add_argument("--product-type")
    p.add_argument("--development-region")
    p.add_argument("--compress-pngs", choices=("yes","no"), default="yes")
    p.add_argument("--enable-on-demand-resources", choices=("yes","no"), default="no")
    p.add_argument("--print-contents", action="store_true")
    p.add_argument("--version", action="store_true")
    p.add_argument("--capabilities", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    ns = parser().parse_args(argv)
    if ns.version:
        print(VERSION)
        return 0
    if ns.capabilities:
        from .capabilities import capability_report
        print(json.dumps(capability_report(), indent=2, ensure_ascii=False))
        return 0
    if ns.output is None:
        print("actool: error: --compile is required", file=sys.stderr)
        return 1
    result = compile_catalogs(ns.inputs, CompileOptions(
        output=ns.output,
        platform=ns.platform,
        minimum_deployment_target=ns.minimum_deployment_target,
        app_icon=ns.app_icon,
        accent_color=ns.accent_color,
        launch_image=ns.launch_image,
        partial_info_plist=ns.output_partial_info_plist,
        warnings=ns.warnings == "yes",
        errors=ns.errors == "yes",
        notices=ns.notices == "yes",
        target_devices=tuple(ns.target_device),
        filter_for_device_model=ns.filter_for_device_model,
        filter_for_device_os_version=ns.filter_for_device_os_version,
        product_type=ns.product_type,
        development_region=ns.development_region,
        compress_pngs=ns.compress_pngs == "yes",
        enable_on_demand_resources=ns.enable_on_demand_resources == "yes",
    ))
    for diagnostic in result.diagnostics:
        enabled = {
            "warning": ns.warnings == "yes",
            "error": ns.errors == "yes",
            "notice": ns.notices == "yes",
        }.get(diagnostic.severity, True)
        if enabled:
            print(diagnostic.render(), file=sys.stderr)
    if ns.print_contents:
        for output in result.outputs:
            print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
