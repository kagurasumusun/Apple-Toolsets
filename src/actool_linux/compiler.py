from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import plistlib

from .carwriter import (
    app_icon_renditions, build_assets_car, color_rendition, data_rendition,
    heif_rendition, jpeg_rendition, png_rendition, resize_png, svg_renditions, symbol_rendition,
)
from .model import Catalog, Diagnostic, load_catalog
from .appicons import app_icon_sidecar_specs


@dataclass
class CompileOptions:
    output: Path
    platform: str | None = None
    minimum_deployment_target: str | None = None
    app_icon: str | None = None
    accent_color: str | None = None
    launch_image: str | None = None
    partial_info_plist: Path | None = None
    warnings: bool = True
    errors: bool = True
    notices: bool = True


@dataclass
class CompileResult:
    catalogs: list[Catalog]
    diagnostics: list[Diagnostic]
    outputs: list[Path]

    @property
    def ok(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)


def _partial_info(catalogs: Iterable[Catalog], options: CompileOptions) -> dict[str, object]:
    result: dict[str, object] = {}
    names = {asset.name for catalog in catalogs for asset in catalog.assets}
    if options.app_icon and options.app_icon in names:
        primary = {
            "CFBundleIconFiles": ["AppIcon60x60"],
            "CFBundleIconName": options.app_icon,
        }
        result["CFBundleIcons"] = {"CFBundlePrimaryIcon": primary}
        if (options.platform or "").lower() in ("iphoneos", "iphonesimulator", "ios"):
            result["CFBundleIcons~ipad"] = {
                "CFBundlePrimaryIcon": {
                    "CFBundleIconFiles": ["AppIcon60x60", "AppIcon76x76"],
                    "CFBundleIconName": options.app_icon,
                }
            }
    return result


def compile_catalogs(inputs: list[Path], options: CompileOptions) -> CompileResult:
    catalogs = [load_catalog(path) for path in inputs]
    diagnostics = [item for catalog in catalogs for item in catalog.diagnostics]
    outputs: list[Path] = []

    if not inputs:
        diagnostics.append(Diagnostic("error", "no input asset catalogs"))
    if options.app_icon and not any(
        asset.kind == "app-icon" and asset.name == options.app_icon
        for catalog in catalogs for asset in catalog.assets
    ):
        diagnostics.append(Diagnostic("warning", f"app icon set '{options.app_icon}' was not found"))
    if options.launch_image and not any(
        asset.kind == "launch-image" and asset.name == options.launch_image
        for catalog in catalogs for asset in catalog.assets
    ):
        diagnostics.append(Diagnostic("warning", f"launch image set '{options.launch_image}' was not found"))

    if not any(item.severity == "error" for item in diagnostics):
        options.output.mkdir(parents=True, exist_ok=True)
        if options.partial_info_plist:
            options.partial_info_plist.parent.mkdir(parents=True, exist_ok=True)
            with options.partial_info_plist.open("wb") as stream:
                plistlib.dump(_partial_info(catalogs, options), stream, fmt=plistlib.FMT_BINARY)
            outputs.append(options.partial_info_plist)

        assets = [asset for catalog in catalogs for asset in catalog.assets]
        if assets and all(len(asset.entries) == 1 for asset in assets):
            renditions = []
            for asset in assets:
                entry = asset.entries[0]
                if asset.kind == "color":
                    try:
                        color = entry["color"]
                        color_space = str(color.get("color-space"))
                        if color_space not in ("srgb", "display-p3"):
                            raise ValueError("only sRGB and Display P3 colors are enabled")
                        components = color["components"]
                        values = [float(components[name]) for name in ("red", "green", "blue", "alpha")]
                        renditions.append(color_rendition(asset.name, *values, color_space=color_space))
                    except (KeyError, TypeError, ValueError) as exc:
                        diagnostics.append(Diagnostic("error", f"invalid color entry: {exc}", asset.directory))
                    continue

                filename = entry.get("filename")
                if not isinstance(filename, str):
                    diagnostics.append(Diagnostic("error", "asset entry has no filename", asset.directory))
                    continue
                source = asset.directory / filename
                if not source.is_file():
                    diagnostics.append(Diagnostic("error", f"asset file is missing: {filename}", asset.directory))
                elif asset.kind == "launch-image" and options.launch_image == asset.name:
                    version = str(entry.get("minimum-system-version", "7.0"))
                    version_tag = "".join(ch for ch in version if ch.isdigit()).ljust(3, "0")
                    scale_text = str(entry.get("scale", "1x"))
                    scale_suffix = "" if scale_text == "1x" else f"@{scale_text}"
                    idiom_suffix = "~ipad" if entry.get("idiom") == "ipad" else ""
                    launch_path = options.output / f"{asset.name}-{version_tag}{scale_suffix}{idiom_suffix}.png"
                    launch_path.write_bytes(source.read_bytes())
                    outputs.append(launch_path)
                elif asset.kind == "app-icon":
                    try:
                        source_png = source.read_bytes()
                        renditions.extend(app_icon_renditions(asset.name, source_png, filename, platform=options.platform or "iphoneos"))
                        # Current iOS actool emits these legacy compatibility
                        # sidecars in addition to the modern named AppIcon CAR.
                        sidecars = app_icon_sidecar_specs(options.platform or "iphoneos")
                        for sidecar_name, width, height in sidecars:
                            sidecar = options.output / sidecar_name
                            sidecar.write_bytes(resize_png(source_png, width, height))
                            outputs.append(sidecar)
                    except ValueError as exc:
                        diagnostics.append(Diagnostic("error", f"invalid AppIcon: {exc}", asset.directory))
                elif asset.kind == "data":
                    renditions.append(data_rendition(
                        asset.name, source.read_bytes(),
                        str(entry.get("universal-type-identifier", "public.data")),
                    ))
                elif asset.kind == "image" and source.suffix.lower() in (".jpg", ".jpeg"):
                    renditions.append(jpeg_rendition(asset.name, source.read_bytes(), filename))
                elif asset.kind == "image" and source.suffix.lower() in (".heif", ".heic"):
                    renditions.append(heif_rendition(asset.name, source.read_bytes(), filename))
                elif asset.kind == "image" and source.suffix.lower() == ".png":
                    try:
                        renditions.append(png_rendition(asset.name, source.read_bytes(), filename))
                    except ValueError as exc:
                        diagnostics.append(Diagnostic("error", f"PNG deepmap limitation: {exc}", asset.directory))
                elif asset.kind == "symbol" and source.suffix.lower() == ".svg":
                    try:
                        renditions.append(symbol_rendition(asset.name, source.read_bytes(), filename))
                    except ValueError as exc:
                        diagnostics.append(Diagnostic("error", f"symbol SVG limitation: {exc}", asset.directory))
                elif asset.kind == "image" and source.suffix.lower() == ".svg":
                    try:
                        renditions.extend(svg_renditions(asset.name, source.read_bytes(), filename))
                    except ValueError as exc:
                        diagnostics.append(Diagnostic("error", f"SVG vector limitation: {exc}", asset.directory))
                else:
                    diagnostics.append(Diagnostic(
                        "error", "the enabled encoder supports data sets, sRGB/Display P3 colors, JPEG/HEIF images, and the verified 1x1 GA8 PNG subset; PDF vector output remains experimental", 
                        asset.directory,
                    ))

            if renditions and not any(item.severity == "error" for item in diagnostics):
                car_path = options.output / "Assets.car"
                car_path.write_bytes(build_assets_car(
                    renditions,
                    platform=options.platform or "macosx",
                    target=options.minimum_deployment_target or "13.0",
                ))
                outputs.append(car_path)
        else:
            diagnostics.append(Diagnostic(
                "error",
                "every enabled asset must currently contain exactly one rendition; multi-scale and appearance variants remain oracle-gated",
            ))
    return CompileResult(catalogs, diagnostics, outputs)
