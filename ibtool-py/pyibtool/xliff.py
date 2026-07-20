"""
ibtool の XLIFF 出力・取り込み (ローカライズ用)

Apple ibtool 互換の XLIFF 1.2 + Apple 独自 namespace:
  - xmlns="urn:oasis:names:tc:xliff:document:1.2"
  - xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  - xmlns:ib="com.apple.InterfaceBuilder3"
  - <file original="..." datatype="x-com.apple.InterfaceBuilder3.CocoaTouch.XIB"
         tool-id="com.apple.ibtool" source-language="en" target-language="ja">
  - <header><tool tool-id="com.apple.ibtool" tool-name="ibtool" tool-version="..."/></header>
  - <body>
    - <group ib:member-type="objects">...</group>
    - <group ib:member-type="connections">...</group>
  - </body>
  - localizable な trans-unit は xib の各 object の <text>/<title> 等から
"""

from typing import List, Optional
from xml.etree import ElementTree as ET

from .xibdoc import XIBDocument, XIBObject, XIBElement
from .strings import LOCALIZABLE_KEYS, _walk, _walk_children


NS = "urn:oasis:names:tc:xliff:document:1.2"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_IB = "com.apple.InterfaceBuilder3"


def export_xliff(doc: XIBDocument, source_lang: str, target_lang: Optional[str],
                 empty_targets: bool = False,
                 apple_compat: bool = True,
                 original_filename: str = None) -> str:
    """xib から XLIFF を生成

    apple_compat=True (default): Apple ibtool 互換の namespace / structure
    apple_compat=False: 標準 XLIFF 1.2 (trans-unit のみ)
    """
    if apple_compat:
        return _export_xliff_apple(doc, source_lang, target_lang, empty_targets,
                                    original_filename=original_filename)
    return _export_xliff_standard(doc, source_lang, target_lang, empty_targets)


def _export_xliff_apple(doc: XIBDocument, source_lang: str, target_lang: Optional[str],
                        empty_targets: bool,
                        original_filename: str = None) -> str:
    """Apple 互換 XLIFF 出力"""
    ET.register_namespace("", NS)
    ET.register_namespace("xsi", NS_XSI)
    ET.register_namespace("ib", NS_IB)

    root = ET.Element("{%s}xliff" % NS, {
        "version": "1.2",
        "{%s}schemaLocation" % NS_XSI:
            "%s xliff-core-1.2-transitional.xsd" % NS,
    })
    # original: ファイル名 (Apple 慣例) または doc_type
    original = original_filename or "document"
    file_attrs = {
        "original": original,
        "datatype": "x-" + (doc.doc_type or "com.apple.InterfaceBuilder3.CocoaTouch.XIB"),
        "tool-id": "com.apple.ibtool",
        "source-language": source_lang,
    }
    if target_lang:
        file_attrs["target-language"] = target_lang
    file_el = ET.SubElement(root, "{%s}file" % NS, file_attrs)
    # header
    header = ET.SubElement(file_el, "{%s}header" % NS)
    ET.SubElement(header, "{%s}tool" % NS, {
        "tool-id": "com.apple.ibtool",
        "tool-name": "ibtool",
        "tool-version": "26000",  # pyibtool 内部バージョン
    })
    # body
    body = ET.SubElement(file_el, "{%s}body" % NS)

    # member-type=objects
    group_objects = ET.SubElement(body, "{%s}group" % NS, {
        "{%s}member-type" % NS_IB: "objects",
    })
    for o in doc.objects:
        # object の class 名 (xib tag → Cocoa class)
        cc = o.attributes.get("customClass") or o.tag
        grp = ET.SubElement(group_objects, "{%s}group" % NS, {
            "{%s}object-id" % NS_IB: o.id,
            "{%s}class" % NS_IB: cc,
        })
        for e in _walk(o):
            for k in LOCALIZABLE_KEYS:
                if k in e.attributes:
                    v = e.attributes[k]
                    if v and v.strip() or empty_targets:
                        tu = ET.SubElement(grp, "{%s}trans-unit" % NS, {
                            "id": "%s.%s" % (o.id, k),
                        })
                        src = ET.SubElement(tu, "{%s}source" % NS)
                        src.text = v
                        if empty_targets:
                            tgt = ET.SubElement(tu, "{%s}target" % NS)
                            tgt.text = ""

    # member-type=connections
    if doc.connections:
        group_conn = ET.SubElement(body, "{%s}group" % NS, {
            "{%s}member-type" % NS_IB: "connections",
        })
        for c in doc.connections:
            ET.SubElement(group_conn, "{%s}group" % NS, {
                "{%s}object-id" % NS_IB: c.label,
                "{%s}class" % NS_IB: "IBCocoaTouchOutletConnection"
                if c.type == "outlet" else "IBCocoaTouchActionConnection",
            })

    # XLIFF namespace prefix を出力
    xml_decl = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body_str = ET.tostring(root, encoding="unicode")
    return xml_decl + body_str


def _export_xliff_standard(doc: XIBDocument, source_lang: str, target_lang: Optional[str],
                           empty_targets: bool) -> str:
    """標準 XLIFF 1.2 出力"""
    root = ET.Element("xliff", {
        "version": "1.2",
        "xmlns": NS,
    })
    file_el = ET.SubElement(root, "file", {
        "original": "document",
        "source-language": source_lang,
        "datatype": "plist",
    })
    if target_lang:
        file_el.set("target-language", target_lang)
    body = ET.SubElement(file_el, "body")

    for o in doc.objects:
        for e in _walk(o):
            for k in LOCALIZABLE_KEYS:
                if k in e.attributes:
                    v = e.attributes[k]
                    if v and v.strip() or empty_targets:
                        tu = ET.SubElement(body, "trans-unit", {
                            "id": "%s.%s" % (o.id, k),
                        })
                        src = ET.SubElement(tu, "source")
                        src.text = v
                        if empty_targets:
                            tgt = ET.SubElement(tu, "target")
                            tgt.text = ""
    return ET.tostring(root, encoding="unicode", xml_declaration=False)


def apply_xliff(doc: XIBDocument, xliff_text: str) -> None:
    """XLIFF を xib に適用"""
    root = ET.fromstring(xliff_text)
    for tu in root.iter("{%s}trans-unit" % NS):
        tid = tu.get("id", "")
        tgt = tu.find("{%s}target" % NS)
        if tgt is not None and tgt.text is not None:
            # 形式: "OBJECTID.KEY"
            if "." in tid:
                oid, key = tid.rsplit(".", 1)
                for o in doc.objects:
                    if o.id == oid:
                        for e in _walk(o):
                            if key in e.attributes:
                                e.attributes[key] = tgt.text
                                break
