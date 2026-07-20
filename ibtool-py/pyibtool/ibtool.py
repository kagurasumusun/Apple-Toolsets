"""
pyibtool: Apple ibtool の pure Python による CLI 実装

Mac 非依存 / pure Python / no third-party deps
"""

from __future__ import annotations
import argparse
import sys
import os
import io
import plistlib
import json
from typing import List, Optional, Tuple

from .xibdoc import (
    XIBDocument, parse_xib_text, serialize_xib, DOCTYPE_COCOATOUCH_XIB,
    DOCTYPE_COCOATOUCH_STORYBOARD, DOCTYPE_COCOA_XIB, DOCTYPE_APPLETV_XIB,
    DOCTYPE_APPLETV_STORYBOARD,
)
from . import dump
from . import strings
from . import xliff


# ibtool のバージョン (本実装)
IBTOOL_VERSION_BUNDLE = "0"
IBTOOL_VERSION_SHORT = "1.0.0"


# エラー出力フォーマット: plist XML
def emit_error(msg: str, code: int = 1):
    """ibtool 互換のエラー出力 (plist XML 形式)"""
    pl = {
        "com.apple.ibtool.errors": [
            {"description": msg}
        ]
    }
    out = plistlib.dumps(pl, fmt=plistlib.FMT_XML)
    if isinstance(sys.stdout, io.BytesIO):
        sys.stdout.write(out)
    else:
        sys.stdout.write(out.decode("utf-8") if isinstance(out, bytes) else out)
    sys.stdout.flush()
    return code


def emit_warning(msg: str):
    """Apple ibtool --print-warnings 互換の plist XML 出力 (stdout)"""
    pl = {
        "com.apple.ibtool.warnings": [
            {"description": msg}
        ]
    }
    out = plistlib.dumps(pl, fmt=plistlib.FMT_XML)
    if isinstance(sys.stdout, io.BytesIO):
        sys.stdout.write(out)
    else:
        sys.stdout.write(out.decode("utf-8") if isinstance(out, bytes) else out)
    sys.stdout.flush()


def emit_usage_and_exit(msg: str = "Error: No arguments specified, please consult `man ibtool` in Terminal.", code: int = 64):
    """ibtool の「no args」エラー (exit 64)"""
    # stderr に "Error: ..." メッセージ
    if isinstance(sys.stderr, io.BytesIO):
        sys.stderr.write((msg + "\n").encode("utf-8"))
    else:
        sys.stderr.write(msg + "\n")
    sys.stderr.flush()
    return code


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args, opts = parse_args(argv)
    if args is None:
        return opts  # error code
    return run(args, opts)


def parse_args(argv: List[str]):
    """ibtool 互換の argv パーサ
    戻り値: (args_namespace, opts_dict) or (None, error_code)"""
    if not argv:
        code = emit_usage_and_exit()
        return None, code

    # まず手動でパース (ibtool の引数スタイル)
    # ibtool は「--key value」または「--key=value」形式
    parser = argparse.ArgumentParser(prog="ibtool", add_help=False)
    # 未知の引数を受け入れる
    parser.add_argument("--write", dest="write", metavar="PATH")
    parser.add_argument("--output-format", dest="output_format",
                        choices=["xml1", "binary1", "human-readable-text"])
    parser.add_argument("--compile", dest="compile", metavar="PATH")
    parser.add_argument("--flatten", dest="flatten", metavar="BOOL")
    parser.add_argument("--module", dest="module", metavar="NAME")
    parser.add_argument("--strip", dest="strip", action="store_true")
    parser.add_argument("--bundle", dest="bundle", metavar="PATH", action="append")
    parser.add_argument("--plugin", dest="plugin", metavar="PATH", action="append")
    parser.add_argument("--plugin-dir", dest="plugin_dir", metavar="PATH", action="append")
    parser.add_argument("--minimum-deployment-target", dest="min_deployment_target", metavar="VER")
    parser.add_argument("--deployment-target", dest="deployment_target", metavar="VER")
    parser.add_argument("--no-pipeline", dest="no_pipeline", action="store_true")
    parser.add_argument("--no-warnings", dest="no_warnings", action="store_true")
    parser.add_argument("--print-errors", dest="print_errors", action="store_true")
    parser.add_argument("--assert-immutable", dest="assert_immutable", action="store_true")
    parser.add_argument("--no-flatten", dest="no_flatten", action="store_true")
    parser.add_argument("--output-encoding", dest="output_encoding", metavar="ENC")
    parser.add_argument("--link", dest="link", metavar="PATH", action="append")
    parser.add_argument("--stack-trace", dest="stack_trace", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    parser.add_argument("--quiet", dest="quiet", action="store_true")
    parser.add_argument("--validation", dest="validation", metavar="LEVEL")
    parser.add_argument("--no-default-rules", dest="no_default_rules", action="store_true")
    parser.add_argument("--output-format-version", dest="output_format_version", metavar="VER")
    parser.add_argument("--screen-scale", dest="screen_scale", metavar="SCALE")
    parser.add_argument("--localization", dest="localization", metavar="LANG")
    parser.add_argument("--language", dest="language", metavar="LANG")
    parser.add_argument("--locales", dest="locales", metavar="LOCALES")
    parser.add_argument("--resource-rules", dest="resource_rules", metavar="PATH")
    parser.add_argument("--thinning", dest="thinning", metavar="ARCH")
    parser.add_argument("--flatten-recursively", dest="flatten_recursively", action="store_true")
    parser.add_argument("--serialize", dest="serialize", metavar="PATH")
    parser.add_argument("--no-relax-link-validation", dest="no_relax_link_validation", action="store_true")
    parser.add_argument("--relax-link-validation", dest="relax_link_validation", action="store_true")
    parser.add_argument("--no-color", dest="no_color", action="store_true")
    parser.add_argument("--pretty", dest="pretty", action="store_true")
    parser.add_argument("--read", dest="read", metavar="PATH")
    parser.add_argument("--validate", dest="validate", action="store_true")
    parser.add_argument("--verify", dest="verify", action="store_true")
    parser.add_argument("--cache", dest="cache", metavar="PATH")
    parser.add_argument("--no-cache", dest="no_cache", action="store_true")
    parser.add_argument("--primary-language", dest="primary_language", metavar="LANG")
    parser.add_argument("--development-language", dest="development_language", metavar="LANG")
    parser.add_argument("--known-regions", dest="known_regions", metavar="REGIONS")
    parser.add_argument("--fallback-language", dest="fallback_language", metavar="LANG")
    parser.add_argument("--default-language", dest="default_language", metavar="LANG")
    parser.add_argument("--no-include-storyboards", dest="no_include_storyboards", action="store_true")
    parser.add_argument("--include-storyboards", dest="include_storyboards", action="store_true")
    parser.add_argument("--intents", dest="intents", metavar="PATH")
    parser.add_argument("--no-intents", dest="no_intents", action="store_true")
    parser.add_argument("--ibwarnings", dest="ibwarnings", metavar="PATH")
    parser.add_argument("--ibnotices", dest="ibnotices", metavar="PATH")
    parser.add_argument("--no-module-warnings", dest="no_module_warnings", action="store_true")
    parser.add_argument("--output-path", dest="output_path", metavar="PATH")
    parser.add_argument("--ignore-missing-modules", dest="ignore_missing_modules", action="store_true")
    parser.add_argument("--module-path", dest="module_path", metavar="PATH")
    parser.add_argument("--headers-path", dest="headers_path", metavar="PATH")
    parser.add_argument("--frameworks-path", dest="frameworks_path", metavar="PATH")
    parser.add_argument("--sdk-path", dest="sdk_path", metavar="PATH")
    parser.add_argument("--toolchain", dest="toolchain", metavar="NAME")
    parser.add_argument("--platform-name", dest="platform_name", metavar="NAME")
    parser.add_argument("--platform-path", dest="platform_path", metavar="PATH")
    parser.add_argument("--print-warnings", dest="print_warnings", action="store_true")
    parser.add_argument("--sdkroot", dest="sdkroot", metavar="PATH")
    parser.add_argument("--target", dest="target", metavar="TARGET")
    parser.add_argument("--allow-obj-c-modules", dest="allow_objc_modules", action="store_true")
    parser.add_argument("--no-allow-obj-c-modules", dest="no_allow_objc_modules", action="store_true")
    parser.add_argument("--enable-obj-c-modules", dest="enable_objc_modules", action="store_true")
    parser.add_argument("--disable-obj-c-modules", dest="disable_objc_modules", action="store_true")
    parser.add_argument("--runtime-args", dest="runtime_args", metavar="ARGS")
    parser.add_argument("--dependency-info", dest="dependency_info", metavar="PATH")
    parser.add_argument("--emit-dependency-info", dest="emit_dependency_info", action="store_true")
    parser.add_argument("--no-emit-dependency-info", dest="no_emit_dependency_info", action="store_true")
    parser.add_argument("--product-type", dest="product_type", metavar="TYPE")
    parser.add_argument("--track-changes", dest="track_changes", action="store_true")
    parser.add_argument("--no-track-changes", dest="no_track_changes", action="store_true")
    parser.add_argument("--ib-class-info", dest="ib_class_info", metavar="PATH")
    parser.add_argument("--emit-ib-class-info", dest="emit_ib_class_info", action="store_true")
    parser.add_argument("--doc", dest="doc", action="store_true")
    parser.add_argument("--docs", dest="docs", action="store_true")
    parser.add_argument("--detailed-warnings", dest="detailed_warnings", action="store_true")
    parser.add_argument("--no-detailed-warnings", dest="no_detailed_warnings", action="store_true")
    parser.add_argument("--print-deprecation-warnings", dest="print_deprecation_warnings", action="store_true")
    parser.add_argument("--no-print-deprecation-warnings", dest="no_print_deprecation_warnings", action="store_true")
    parser.add_argument("--strict", dest="strict", action="store_true")
    parser.add_argument("--no-strict", dest="no_strict", action="store_true")
    parser.add_argument("--region", dest="region", metavar="REGION")
    parser.add_argument("--regions", dest="regions", metavar="REGIONS")
    parser.add_argument("--input-format", dest="input_format", metavar="FORMAT")
    parser.add_argument("--output-format-options", dest="output_format_options", metavar="OPTS")
    parser.add_argument("--load-plugin", dest="load_plugin", metavar="PATH", action="append")
    parser.add_argument("--arch", dest="arch", metavar="ARCH")
    parser.add_argument("--universal", dest="universal", action="store_true")
    parser.add_argument("--no-universal", dest="no_universal", action="store_true")
    parser.add_argument("--platform", dest="platform", metavar="PLATFORM")
    parser.add_argument("--build", dest="build", metavar="BUILD")
    parser.add_argument("--deployment-os", dest="deployment_os", metavar="OS")
    parser.add_argument("--minimum-os", dest="minimum_os", metavar="OS")
    parser.add_argument("--target-os", dest="target_os", metavar="OS")
    parser.add_argument("--device", dest="device", metavar="DEVICE")
    parser.add_argument("--os-version", dest="os_version", metavar="VER")
    parser.add_argument("--xros", dest="xros", action="store_true")
    parser.add_argument("--tvos", dest="tvos", action="store_true")
    parser.add_argument("--watchos", dest="watchos", action="store_true")
    parser.add_argument("--ios", dest="ios", action="store_true")
    parser.add_argument("--macos", dest="macos", action="store_true")
    parser.add_argument("--visionos", dest="visionos", action="store_true")
    parser.add_argument("--catalyst", dest="catalyst", action="store_true")
    parser.add_argument("--appletvos", dest="appletvos", action="store_true")
    parser.add_argument("--bridgeos", dest="bridgeos", action="store_true")
    parser.add_argument("--driverkit", dest="driverkit", action="store_true")
    parser.add_argument("--xrsdk", dest="xrsdk", metavar="PATH")
    parser.add_argument("--iphonesimulatorsdk", dest="iphonesimulatorsdk", metavar="PATH")
    parser.add_argument("--appletvsimulatorsdk", dest="appletvsimulatorsdk", metavar="PATH")
    parser.add_argument("--watchsimulatorsdk", dest="watchsimulatorsdk", metavar="PATH")
    parser.add_argument("--xrsimulatorsdk", dest="xrsimulatorsdk", metavar="PATH")
    parser.add_argument("--macosx-sdk", dest="macosx_sdk", metavar="PATH")
    parser.add_argument("--embedded", dest="embedded", action="store_true")
    parser.add_argument("--simulator", dest="simulator", action="store_true")
    parser.add_argument("--device-family", dest="device_family", metavar="FAM")
    parser.add_argument("--previous-file", dest="previous_file", metavar="PATH")
    parser.add_argument("--incremental-file", dest="incremental_file", metavar="PATH")
    parser.add_argument("--localize-incremental", dest="localize_incremental", action="store_true")
    parser.add_argument("--reference-external-strings-file", dest="ref_ext_strings", action="store_true")
    parser.add_argument("--companion-strings-file", dest="companion_strings", metavar="LOC:FILE", action="append")
    parser.add_argument("--import", dest="import_plist", metavar="PATH")
    parser.add_argument("--import-strings-file", dest="import_strings", metavar="PATH")
    parser.add_argument("--import-xliff", dest="import_xliff", metavar="PATH")
    parser.add_argument("--export", dest="export", metavar="PATH")
    parser.add_argument("--export-strings-file", dest="export_strings", metavar="PATH")
    parser.add_argument("--export-xliff", dest="export_xliff", metavar="PATH")
    parser.add_argument("--generate-strings-file", dest="generate_strings", metavar="PATH")
    parser.add_argument("--generate-xliff", dest="generate_xliff", metavar="PATH")
    parser.add_argument("--source-language", dest="source_language", metavar="LANG")
    parser.add_argument("--target-language", dest="target_language", metavar="LANG")
    parser.add_argument("--convert", dest="convert", metavar="OLD-NEW")
    parser.add_argument("--upgrade", dest="upgrade", action="store_true")
    parser.add_argument("--remove-plugin-dependencies", dest="remove_plugin_deps", action="store_true")
    parser.add_argument("--enable-auto-layout", dest="enable_auto_layout", action="store_true")
    parser.add_argument("--update-frames", dest="update_frames", action="store_true")
    parser.add_argument("--update-constraints", dest="update_constraints", action="store_true")
    parser.add_argument("--warnings", dest="warnings", action="store_true")
    parser.add_argument("--errors", dest="errors", action="store_true")
    parser.add_argument("--notices", dest="notices", action="store_true")
    parser.add_argument("--localizable-strings", dest="loc_strings", action="store_true")
    parser.add_argument("--localizable-stringarrays", dest="loc_stringarrays", action="store_true")
    parser.add_argument("--localizable-geometry", dest="loc_geometry", action="store_true")
    parser.add_argument("--localizable-other", dest="loc_other", action="store_true")
    parser.add_argument("--localizable-to-many-relationships", dest="loc_to_many", action="store_true")
    parser.add_argument("--localizable-all", dest="loc_all", action="store_true")
    parser.add_argument("--objects", dest="objects", action="store_true")
    parser.add_argument("--hierarchy", dest="hierarchy", action="store_true")
    parser.add_argument("--connections", dest="connections", action="store_true")
    parser.add_argument("--classes", dest="classes", action="store_true")
    parser.add_argument("--version-history", dest="version_history", action="store_true")
    parser.add_argument("--all", dest="all_dump", action="store_true")
    parser.add_argument("--version", dest="version", action="store_true")
    parser.add_argument("--target-device", dest="target_device", metavar="DEV")
    parser.add_argument("--target-device-family", dest="target_device_family", metavar="IDS")
    parser.add_argument("--sdk", dest="sdk", metavar="SDK")
    parser.add_argument("--auto-activate-custom-fonts", dest="auto_activate", action="store_true")
    parser.add_argument("--store", dest="store", action="store_true")
    parser.add_argument("--store-version", dest="store_version", metavar="VER")
    parser.add_argument("--store-build", dest="store_build", metavar="BUILD")
    parser.add_argument("--agent-name", dest="agent_name", metavar="NAME")

    # ibtool 互換: 位置引数 = 入力ファイル
    parser.add_argument("input", nargs="?")

    # 未知の引数を ibtool 流に plist エラーで返す
    known_opts = set()
    for action in parser._actions:
        if action.option_strings:
            for opt in action.option_strings:
                known_opts.add(opt)
    # argv 走査して --unknown など未定義を検出
    for tok in argv:
        if tok.startswith("--"):
            opt = tok.split("=", 1)[0]
            if opt not in known_opts and opt != "--":
                emit_error("Unknown argument '%s'." % opt, code=1)
                return None, 1
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        # argparse がエラーで exit
        return None, 1
    return args, None


def run(args, opts) -> int:
    if args.version:
        return cmd_version()
    if not args.input:
        return emit_usage_and_exit()
    if not os.path.exists(args.input):
        return emit_error("Interface Builder could not open the document \"%s\" because it does not exist." %
                          args.input, code=1)
    # --agent-name は portable 実装では no-op (Apple ibtool の agent は Mac 依存)
    # 認識だけしてフラグとして保持
    if args.agent_name:
        # 何もしない (本実装は agent 機能なし、man ページ互換のため認識だけ)
        pass

    # 入力読込
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            txt = f.read()
        doc = parse_xib_text(txt)
    except Exception as e:
        return emit_error("Interface Builder could not open the document \"%s\". %s" % (args.input, e), code=1)

    # 各コマンド
    if args.export_strings:
        return cmd_export_strings(doc, args.export_strings)
    if args.generate_strings:
        return cmd_generate_strings(doc, args.generate_strings)
    if args.export_xliff:
        return cmd_export_xliff(doc, args.export_xliff,
                                args.source_language or "en",
                                args.target_language, args)
    if args.generate_xliff:
        return cmd_generate_xliff(doc, args.generate_xliff,
                                  args.source_language or "en",
                                  args.target_language, args)
    if args.export:
        return cmd_export(doc, args.export, args)
    if args.convert:
        return cmd_convert(doc, args.convert, args)
    if args.upgrade:
        return cmd_upgrade(doc, args)
    if args.remove_plugin_deps:
        return cmd_remove_plugin_deps(doc, args)
    if args.enable_auto_layout:
        return cmd_enable_auto_layout(doc, args)
    if args.update_frames:
        return cmd_update_frames(doc, args)
    if args.update_constraints:
        return cmd_update_constraints(doc, args)
    if args.localize_incremental:
        return cmd_localize_incremental(doc, args)
    if args.import_strings:
        return cmd_import_strings(doc, args.import_strings, args)
    if args.import_xliff:
        return cmd_import_xliff(doc, args.import_xliff, args)
    if args.import_plist:
        return cmd_import(doc, args.import_plist, args)
    if args.compile:
        return cmd_compile(doc, args)
    if args.strip:
        # --strip is a boolean flag that requires --compile or --write to specify output
        return cmd_strip(doc, args)
    if args.plugin:
        return cmd_plugin(doc, args)
    if args.plugin_dir:
        return cmd_plugin_dir(doc, args)
    if args.bundle:
        return cmd_bundle(doc, args)
    if args.warnings or args.errors or args.notices or args.all_dump or \
       args.objects or args.hierarchy or args.connections or args.classes or \
       args.version_history or args.loc_strings or args.loc_stringarrays or \
       args.loc_geometry or args.loc_other or args.loc_to_many or args.loc_all:
        return cmd_dump(doc, args)
    if args.output_format or args.write:
        return cmd_write_xib(doc, args)
    # デフォルト = xib を標準出力へ (人間が読める形式)
    return cmd_write_xib(doc, args)


def cmd_version() -> int:
    pl = {
        "com.apple.ibtool.version": {
            "bundle-version": IBTOOL_VERSION_BUNDLE,
            "short-bundle-version": IBTOOL_VERSION_SHORT,
        }
    }
    out = plistlib.dumps(pl, fmt=plistlib.FMT_XML)
    sys.stdout.write(out.decode("utf-8") if isinstance(out, bytes) else out)
    return 0


def cmd_export_strings(doc: XIBDocument, path: str) -> int:
    data = strings.generate_strings(doc)
    if path == "-":
        sys.stdout.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    return 0


def cmd_generate_strings(doc: XIBDocument, path: str) -> int:
    # generate-strings-file = 空文字列で output を生成
    data = strings.generate_strings(doc, empty_values=True)
    if path == "-":
        sys.stdout.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    return 0


def cmd_export_xliff(doc: XIBDocument, path: str, src: str, tgt: Optional[str], args) -> int:
    # Apple 互換: file original = 入力ファイル名
    original = os.path.basename(args.input) if hasattr(args, 'input') and args.input else "document"
    data = xliff.export_xliff(doc, src, tgt, original_filename=original)
    if path == "-":
        sys.stdout.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    return 0


def cmd_generate_xliff(doc: XIBDocument, path: str, src: str, tgt: Optional[str], args) -> int:
    original = os.path.basename(args.input) if hasattr(args, 'input') and args.input else "document"
    data = xliff.export_xliff(doc, src, tgt, empty_targets=True, original_filename=original)
    if path == "-":
        sys.stdout.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    return 0


def cmd_export(doc: XIBDocument, plist_path: str, args) -> int:
    """--export: input plist で指定されたクラス/プロパティを書き出し

    Apple ibtool の input plist 形式 (com.apple.ibtool.document.export dict):
      {com.apple.ibtool.document.export: {object_id: {keypath: value}}}

    本実装では両形式に対応:
      1. {className: [prop1, prop2, ...]} (シンプル形式)
      2. {com.apple.ibtool.document.export: {object_id: {keypath: value}}} (Apple 形式)
    """
    with open(plist_path, "rb") as f:
        req = plistlib.load(f)

    out: Dict[str, Any] = {"com.apple.ibtool.document.export": {}}

    # Apple 形式: com.apple.ibtool.document.export dict
    if "com.apple.ibtool.document.export" in req:
        apple_data = req["com.apple.ibtool.document.export"]
        for oid, props in apple_data.items():
            for o in doc.objects:
                if o.id == oid:
                    # Apple 形式: そのまま書き出し
                    out["com.apple.ibtool.document.export"][oid] = props
                    break
    # シンプル形式: {className: [prop1, prop2, ...]}
    else:
        for o in doc.objects:
            cls = o.attributes.get("customClass") or o.tag
            props = req.get(cls, [])
            if not props:
                continue
            d: dict = {}
            for p in props:
                if p in o.attributes:
                    d[p] = o.attributes[p]
            if d:
                out["com.apple.ibtool.document.export"][o.id] = d

    sys.stdout.write(plistlib.dumps(out, fmt=plistlib.FMT_XML).decode("utf-8"))
    return 0


def cmd_import(doc: XIBDocument, plist_path: str, args) -> int:
    """--import: --export で出力した plist を読み込んで xib に反映
    plist 形式: {com.apple.ibtool.document.export: {obj_id: {keypath: value}}}
    """
    if not os.path.exists(plist_path):
        return emit_error("Could not open import plist file: %s" % plist_path, code=1)
    with open(plist_path, "rb") as f:
        req = plistlib.load(f)
    export_dict = req.get("com.apple.ibtool.document.export", {})
    applied = 0
    for oid, props in export_dict.items():
        for o in doc.objects:
            if o.id == oid:
                for k, v in props.items():
                    o.attributes[k] = str(v) if v is not None else ""
                applied += 1
                break
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_convert(doc: XIBDocument, spec: str, args) -> int:
    """--convert OLD-NEW or OLD'*'-NEW

    Apple ibtool のシンタックス (man ページより):
      --convert OldName-NewName      (1:1 変換)
      --convert Old'*'-NewName      (ワイルドカード)

    シェル経由でユーザーが渡す時:
      - bash: --convert 'UI*'-MyUI' → argv = "UI*'-MyUI" (8 chars)
      - shell escape しない: --convert "UI*'-MyUI" → 同じ
      - Apple 内部では ' を special char として扱い、'*-' で split
    仕様: spec の中で '*' を含むかどうかで分岐
      - '*' あり = ワイルドカード:  '*' で split して prefix と new に分割
      - '*' なし = 1:1 変換
    実装の単純化: '*' の前で split し、wildcard フラグを立てる
    """
    prefix = None
    if "*" in spec:
        # ワイルドカード: '*' で split → ['UI', ''-MyUI'] or ['UI*', '-MyUI'] など
        # shell 経由の spec 例: "UI*'-MyUI" (8 chars)
        # → spec.split('*', 1) = ['UI', "'-MyUI"]
        # → prefix = 'UI' (old), new = "'-MyUI" (strip leading ')
        parts = spec.split("*", 1)
        prefix = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        # rest の先頭が "'-" なら取り除く
        if rest.startswith("'-"):
            new = rest[2:]
        elif rest.startswith("-"):
            new = rest[1:]
        else:
            new = rest
    elif "-" in spec:
        # "OldName-NewName"
        old, new = spec.split("-", 1)
        prefix = None
    else:
        return emit_error("Invalid --convert argument: %s" % spec)

    changed = 0
    for o in doc.objects:
        cls = o.attributes.get("customClass") or o.tag
        if prefix is not None:
            # ワイルドカード: prefix で始まる class を new + 残りに置換
            if cls.startswith(prefix):
                new_cls = new + cls[len(prefix):]
                if "customClass" in o.attributes:
                    o.attributes["customClass"] = new_cls
                o.tag = new_cls
                changed += 1
        else:
            if cls == old:
                if "customClass" in o.attributes:
                    o.attributes["customClass"] = new
                o.tag = new
                changed += 1
        # 子要素の class も対象 (xib 内の <outlet> / <action> 等)
        for c in o.children:
            if c.tag in ("outlet", "action", "segue"):
                ccls = c.attributes.get("customClass") or c.tag
                if prefix is not None:
                    if ccls.startswith(prefix):
                        new_cls = new + ccls[len(prefix):]
                        if "customClass" in c.attributes:
                            c.attributes["customClass"] = new_cls
                else:
                    if ccls == old:
                        if "customClass" in c.attributes:
                            c.attributes["customClass"] = new
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_upgrade(doc: XIBDocument, args) -> int:
    """--upgrade: toolsVersion を最新に更新 (Xcode 26 想定)"""
    doc.tools_version = "26000"
    doc.version = "3.0"
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_remove_plugin_deps(doc: XIBDocument, args) -> int:
    """--remove-plugin-dependencies: plugIn 依存を除去"""
    doc.plug_ins = [p for p in doc.plug_ins if p.attributes.get("identifier", "").startswith("com.apple.InterfaceBuilder.IB")]
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_enable_auto_layout(doc: XIBDocument, args) -> int:
    doc.use_autolayout = "YES"
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_update_frames(doc: XIBDocument, args) -> int:
    """--update-frames: フレーム更新 (本実装は noop)"""
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_update_constraints(doc: XIBDocument, args) -> int:
    """--update-constraints: 制約更新 (本実装は noop)"""
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_localize_incremental(doc: XIBDocument, args) -> int:
    if not args.previous_file or not args.incremental_file:
        return emit_error("When specifying --localize-incremental, one MUST provide a --previous-file and an --incremental-file.", code=1)
    # 3-way マージ (本実装は簡略化: incremental をそのままコピー)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_import_strings(doc: XIBDocument, path: str, args) -> int:
    if not os.path.exists(path):
        return emit_error("Could not open strings file: %s" % path, code=1)
    with open(path, "r", encoding="utf-8") as f:
        strings_data = f.read()
    strings.apply_strings(doc, strings_data)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_import_xliff(doc: XIBDocument, path: str, args) -> int:
    if not os.path.exists(path):
        return emit_error("Could not open xliff file: %s" % path, code=1)
    with open(path, "r", encoding="utf-8") as f:
        xliff_data = f.read()
    xliff.apply_xliff(doc, xliff_data)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_compile(doc: XIBDocument, args) -> int:
    """--compile: xib → nib (NIBArchive 形式)"""
    from .nibcompile import compile_to_nib
    try:
        data = compile_to_nib(doc, args)
    except Exception as e:
        return emit_error("Compile failed: %s" % e, code=1)
    out_path = args.compile
    if out_path == "-":
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.write(data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data)
    else:
        # storyboardc はディレクトリ
        if doc.is_storyboard():
            if not os.path.isdir(out_path):
                # 既存のファイルなら削除
                if os.path.exists(out_path):
                    os.unlink(out_path)
                # 親ディレクトリも含めて作成
                os.makedirs(out_path, exist_ok=True)
            # ディレクトリ内に nib ファイル名で書く
            inner_name = os.path.basename(out_path)
            inner_path = os.path.join(out_path, inner_name)
            with open(inner_path, "wb") as f:
                f.write(data)
            return 0
        with open(out_path, "wb") as f:
            f.write(data)
    return 0


def cmd_strip(doc: XIBDocument, args) -> int:
    """--strip: xib → nib (デザイン時要素除去). --compile で出力先指定が必要"""
    if not args.compile:
        return emit_error("--strip requires --compile to specify output path.", code=1)
    from .nibcompile import compile_to_nib
    try:
        data = compile_to_nib(doc, args, strip=True)
    except Exception as e:
        return emit_error("Strip failed: %s" % e, code=1)
    out_path = args.compile
    if out_path == "-":
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(data)
        else:
            if isinstance(sys.stdout, io.BytesIO) or hasattr(sys.stdout, 'write') and sys.stdout.write.__doc__ and 'bytes' in sys.stdout.write.__doc__:
                sys.stdout.write(data)
            else:
                sys.stdout.write(data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data)
    else:
        with open(out_path, "wb") as f:
            f.write(data)
    return 0


def cmd_plugin(doc: XIBDocument, args) -> int:
    """--plugin PATH: 追加 plug-in をロード (Mac 依存 / 該当 SDK 必要)
    本実装は portable: plug-in ディレクトリ内の .xib を再帰的に処理する。
    """
    if not args.plugin:
        return emit_error("--plugin requires a path argument.", code=1)
    for plugin_path in args.plugin:
        if not os.path.exists(plugin_path):
            return emit_error("Plugin path does not exist: %s" % plugin_path, code=1)
        # Plug-in 内の .xib を再帰的に探して読み込む
        for root, _, files in os.walk(plugin_path):
            for fn in files:
                if fn.endswith(".xib") or fn.endswith(".storyboard"):
                    fp = os.path.join(root, fn)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            parse_xib_text(f.read())  # validate
                    except Exception:
                        pass
    # 元の doc をそのまま write
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_plugin_dir(doc: XIBDocument, args) -> int:
    """--plugin-dir PATH: 第 1 階層の全 plug-in をロード (Mac 依存)
    本実装は portable: ディレクトリ内の全 .xib を再帰的に処理する。
    """
    if not args.plugin_dir:
        return emit_error("--plugin-dir requires a path argument.", code=1)
    for plugin_dir in args.plugin_dir:
        if not os.path.exists(plugin_dir):
            return emit_error("Plugin dir does not exist: %s" % plugin_dir, code=1)
        for root, dirs, files in os.walk(plugin_dir):
            # 第 1 階層のみ
            depth = root[len(plugin_dir):].count(os.sep)
            if depth > 0:
                dirs.clear()
                continue
            for fn in files:
                if fn.endswith(".xib") or fn.endswith(".storyboard"):
                    fp = os.path.join(root, fn)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            parse_xib_text(f.read())
                    except Exception:
                        pass
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_bundle(doc: XIBDocument, args) -> int:
    """--bundle PATH: 追加 bundle (Mac 依存)
    本実装は portable: bundle 内の xib を collect して何もしない。
    """
    if not args.bundle:
        return emit_error("--bundle requires a path argument.", code=1)
    for bundle_path in args.bundle:
        if not os.path.exists(bundle_path):
            return emit_error("Bundle path does not exist: %s" % bundle_path, code=1)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(serialize_xib(doc))
    else:
        sys.stdout.write(serialize_xib(doc))
    return 0


def cmd_dump(doc: XIBDocument, args) -> int:
    """--warnings/--errors/--notices/--all/--objects/--hierarchy/--connections/--classes/--version-history/--localizable-* 系のダンプ"""
    out: dict = {}
    if args.all_dump:
        out.update(dump.dump_all(doc))
    else:
        if args.objects:
            out.update(dump.dump_objects(doc))
        if args.hierarchy:
            out.update(dump.dump_hierarchy(doc))
        if args.connections:
            out.update(dump.dump_connections(doc))
        if args.classes:
            out.update(dump.dump_classes(doc))
        if args.version_history:
            out.update(dump.dump_version_history(doc))
        if args.loc_strings:
            out.update(dump.dump_localizable_strings(doc))
        if args.loc_geometry:
            out.update(dump.dump_localizable_geometry(doc))
        if args.loc_stringarrays:
            out.update(dump.dump_localizable_stringarrays(doc))
        if args.loc_other:
            out.update(dump.dump_localizable_other(doc))
        if args.loc_to_many:
            out.update(dump.dump_localizable_to_many_relationships(doc))
        if args.loc_all:
            out.update(dump.dump_localizable_all(doc))
    if args.warnings:
        out["com.apple.ibtool.document.warnings"] = dump.find_warnings(doc)
    if args.errors:
        out["com.apple.ibtool.document.errors"] = dump.find_errors(doc)
    if args.notices:
        out["com.apple.ibtool.document.notices"] = dump.find_notices(doc)

    fmt = args.output_format or "xml1"
    if fmt in ("xml1", "binary1"):
        data = dump.plist_to_bytes(out, fmt)
        if isinstance(sys.stdout, io.BytesIO):
            sys.stdout.write(data)
        elif hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.write(data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data)
    else:
        sys.stdout.write(dump.plist_to_bytes(out, fmt).decode("utf-8"))
    return 0


def cmd_write_xib(doc: XIBDocument, args) -> int:
    """xib を書き出す (デフォルト動作)"""
    fmt = args.output_format or "xml1"
    if fmt in ("xml1",):
        out = serialize_xib(doc)
        if args.write == "-" or (not args.write):
            sys.stdout.write(out)
        else:
            with open(args.write, "w", encoding="utf-8") as f:
                f.write(out)
    elif fmt in ("binary1",):
        # xib を plist binary に
        pl = _xib_to_plist(doc)
        data = plistlib.dumps(pl, fmt=plistlib.FMT_BINARY)
        if args.write == "-" or (not args.write):
            if hasattr(sys.stdout, "buffer"):
                sys.stdout.buffer.write(data)
            else:
                sys.stdout.write(data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data)
        else:
            with open(args.write, "wb") as f:
                f.write(data)
    elif fmt in ("human-readable-text",):
        pl = _xib_to_plist(doc)
        text = dump.human_readable_plist(pl)
        if args.write == "-" or (not args.write):
            sys.stdout.write(text)
        else:
            with open(args.write, "w", encoding="utf-8") as f:
                f.write(text)
    return 0


def _xib_to_plist(doc: XIBDocument) -> dict:
    """xib を plist dict に変換 (--output-format binary1 用)"""
    return {
        "doc.type": doc.doc_type,
        "doc.version": doc.version,
        "doc.toolsVersion": doc.tools_version,
        "doc.targetRuntime": doc.target_runtime,
        "doc.useAutolayout": doc.use_autolayout,
        "objects": [
            {"id": o.id, "tag": o.tag, "attributes": o.attributes}
            for o in doc.objects
        ],
        "connections": [
            {"source": c.source_id, "destination": c.destination_id,
             "label": c.label, "type": c.type}
            for c in doc.connections
        ],
    }


if __name__ == "__main__":
    sys.exit(main())
