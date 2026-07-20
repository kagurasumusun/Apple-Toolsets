"""
xib / storyboard の中立データモデル

XML plist として表現される xib / storyboard を読み書きし、
ibtool の全てのコマンドで操作できる形にする。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Union
import xml.etree.ElementTree as ET
import re


# Document type (Apple の IB ファイル識別子)
DOCTYPE_COCOATOUCH_XIB = "com.apple.InterfaceBuilder3.CocoaTouch.XIB"
DOCTYPE_COCOATOUCH_STORYBOARD = "com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB"
DOCTYPE_COCOA_XIB = "com.apple.InterfaceBuilder3.Cocoa.XIB"
DOCTYPE_APPLETV_XIB = "com.apple.InterfaceBuilder.AppleTV.XIB"
DOCTYPE_APPLETV_STORYBOARD = "com.apple.InterfaceBuilder.AppleTV.Storyboard.XIB"
DOCTYPE_WATCH_XIB = "com.apple.InterfaceBuilder.WatchKit.XIB"
DOCTYPE_XR_XIB = "com.apple.InterfaceBuilder.XR.XIB"


# 多くの xib 要素 tag をまとめて受け付ける
KNOWN_XIB_OBJECT_TAGS = {
    "placeholder", "view", "viewController",
    "tableViewController", "collectionViewController",
    "navigationController", "tabBarController",
    "splitViewController", "pageViewController",
    "object", "button", "label", "imageView",
    "textField", "textView", "stackView", "scrollView",
    "progressView", "activityIndicatorView",
    "segmentedControl", "slider", "stepper",
    "switch", "datePicker", "pickerView",
    "mapView", "webView", "searchBar", "toolbar",
    "barButtonItem", "navigationItem", "menu",
    "scene", "window", "viewControllerPlaceholder",
    # Foundation 等
    "array", "string", "data", "dictionary", "value", "number",
    "bool", "set", "mutableSet", "mutableArray", "mutableString",
    "url", "date", "attributedString",
    # Storyboard
    "segue",
    # 出力で出す tag
    "runtimeoutletconnection", "runtimeactionconnection",
    "color", "font", "image", "rect", "size", "point",
    "customView", "customObject", "control",
    # Apple の xib で現れるタグ (nib2xib の出力含む)
    "outlet", "action", "connections", "layoutGuide",
}


@dataclass
class XIBObject:
    """<objects> 内の 1 要素 (placeholder, view, controller, ...)"""
    id: str
    tag: str  # 例: "view", "placeholder", "button", "viewController"
    attributes: Dict[str, str] = field(default_factory=dict)
    children: List["XIBElement"] = field(default_factory=list)
    text: Optional[str] = None  # text node (string value)


@dataclass
class XIBConnection:
    """<connections> 内の 1 要素"""
    source_id: str
    destination_id: str
    label: str  # 例: "view", "delegate"
    type: str  # "outlet" / "action" / "segue" / "constraint" etc.


@dataclass
class XIBScene:
    """storyboard の <scenes>/<scene>"""
    id: str
    attributes: Dict[str, str] = field(default_factory=dict)
    objects: List[XIBObject] = field(default_factory=list)


@dataclass
class XIBElement:
    """Generic XML element in xib (placeholder, view, rect, color, etc.)"""
    tag: str
    attributes: Dict[str, str] = field(default_factory=dict)
    text: Optional[str] = None
    children: List["XIBElement"] = field(default_factory=list)


@dataclass
class XIBDocument:
    """1 つの xib / storyboard ドキュメント全体"""
    doc_type: str = DOCTYPE_COCOATOUCH_XIB
    version: str = "3.0"
    tools_version: str = ""
    target_runtime: str = "iOS.CocoaTouch"
    property_access_control: str = "none"
    use_autolayout: str = "YES"
    use_trait_collections: str = "YES"
    use_safe_areas: str = "YES"
    color_matched: str = "YES"
    initial_view_controller: Optional[str] = None
    device: Dict[str, str] = field(default_factory=dict)
    dependencies: List[XIBElement] = field(default_factory=list)
    plug_ins: List[XIBElement] = field(default_factory=list)
    capabilities: List[XIBElement] = field(default_factory=list)
    objects: List[XIBObject] = field(default_factory=list)
    connections: List[XIBConnection] = field(default_factory=list)
    scenes: List[XIBScene] = field(default_factory=list)
    root_attributes: Dict[str, str] = field(default_factory=dict)

    def is_storyboard(self) -> bool:
        return "Storyboard" in self.doc_type

    def find_object(self, oid: str) -> Optional[XIBObject]:
        for o in self.objects:
            if o.id == oid:
                return o
        return None

    def collect_classes(self) -> List[Tuple[str, int]]:
        """self.objects を全走査して (class_name, count) のリストを返す。
        class は customClass 属性、または tag 名から取る。"""
        from collections import Counter
        cnt = Counter()
        for o in self.objects:
            cls = o.attributes.get("customClass") or o.tag
            cnt[cls] += 1
        return list(cnt.most_common())


# 制御文字除去 (XML 1.0 で不正な char 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F)
_INVALID_XML_CHARS = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")


def _sanitize_xml_text(s: str) -> str:
    return _INVALID_XML_CHARS.sub("?", s)


def _strip_doctype(s: str) -> str:
    """DOCTYPE 宣言を取り除く (ElementTree は DOCTYPE を扱えない)"""
    m = re.search(r"<!DOCTYPE[^>]*\[.*?\]>", s, re.DOTALL)
    if m:
        s = s[:m.start()] + s[m.end():]
    else:
        m = re.search(r"<!DOCTYPE[^>]+>", s)
        if m:
            s = s[:m.start()] + s[m.end():]
    return s


def parse_xib_text(text: str) -> XIBDocument:
    """XML plist text を XIBDocument に変換"""
    # 制御文字を取り除く
    text = _sanitize_xml_text(text)
    # DOCTYPE を取り除く (ET が DOCTYPE を扱えない)
    text = _strip_doctype(text)
    # BOM を除去
    if text.startswith("\ufeff"):
        text = text[1:]
    # 改行を LF に統一
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 先頭の空行/空白を取り除く
    text = text.lstrip()
    # XML 宣言の前にあるものを切り落とし
    idx = text.find("<?xml")
    if 0 < idx < 200:
        text = text[idx:]
    elif idx < 0:
        # 無い場合 <?xml 宣言を補う (ET は <?xml が無くても動く)
        pass
    # 最初の < から始める
    idx = text.find("<")
    if 0 < idx:
        text = text[idx:]

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        # 失敗: もう一度試す
        # < はそのまま、> をエスケープなどはしない
        try:
            root = ET.fromstring(text.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"failed to parse xib xml: {e}\ntext head: {text[:200]!r}")

    doc = XIBDocument()
    doc.root_attributes = dict(root.attrib)
    doc.doc_type = doc.root_attributes.get("type", DOCTYPE_COCOATOUCH_XIB)
    doc.version = doc.root_attributes.get("version", "3.0")
    doc.tools_version = doc.root_attributes.get("toolsVersion", "")
    doc.target_runtime = doc.root_attributes.get("targetRuntime", "iOS.CocoaTouch")
    doc.property_access_control = doc.root_attributes.get("propertyAccessControl", "none")
    doc.use_autolayout = doc.root_attributes.get("useAutolayout", "YES")
    doc.use_trait_collections = doc.root_attributes.get("useTraitCollections", "YES")
    doc.use_safe_areas = doc.root_attributes.get("useSafeAreas", "YES")
    doc.color_matched = doc.root_attributes.get("colorMatched", "YES")
    doc.initial_view_controller = doc.root_attributes.get("initialViewController")

    for child in root:
        tag = child.tag
        if tag == "device":
            doc.device = dict(child.attrib)
        elif tag == "dependencies":
            for c in child:
                if c.tag == "plugIn":
                    doc.plug_ins.append(_xml_to_element(c))
                elif c.tag == "capability":
                    doc.capabilities.append(_xml_to_element(c))
                else:
                    doc.dependencies.append(_xml_to_element(c))
        elif tag == "objects":
            for c in child:
                if c.tag in KNOWN_XIB_OBJECT_TAGS:
                    doc.objects.append(_xml_to_xibobject(c))
        elif tag == "connections":
            for c in child:
                if c.tag == "connection":
                    doc.connections.append(XIBConnection(
                        source_id=c.attrib.get("source", ""),
                        destination_id=c.attrib.get("destination", ""),
                        label=c.attrib.get("label", ""),
                        type=c.attrib.get("type", "outlet"),
                    ))
        elif tag == "scenes":
            for scene in child:
                if scene.tag == "scene":
                    s = XIBScene(id=scene.attrib.get("sceneID", ""),
                                 attributes=dict(scene.attrib))
                    for obj in scene.iter():
                        if obj.tag in KNOWN_XIB_OBJECT_TAGS:
                            s.objects.append(_xml_to_xibobject(obj))
                    doc.scenes.append(s)
    return doc


def _xml_to_xibobject(el) -> XIBObject:
    obj = XIBObject(
        id=el.attrib.get("id", ""),
        tag=el.tag,
        attributes=dict(el.attrib),
    )
    for c in el:
        obj.children.append(_xml_to_element(c))
    if el.text and el.text.strip():
        obj.text = el.text.strip()
    return obj


def _xml_to_element(el) -> XIBElement:
    e = XIBElement(tag=el.tag, attributes=dict(el.attrib))
    if el.text and el.text.strip():
        e.text = el.text.strip()
    for c in el:
        e.children.append(_xml_to_element(c))
    return e


def serialize_xib(doc: XIBDocument) -> str:
    """XIBDocument を XML plist テキストに"""
    # Build attributes
    attrs = {
        "type": doc.doc_type,
        "version": doc.version,
    }
    if doc.tools_version:
        attrs["toolsVersion"] = doc.tools_version
    if doc.target_runtime:
        attrs["targetRuntime"] = doc.target_runtime
    if doc.property_access_control:
        attrs["propertyAccessControl"] = doc.property_access_control
    if doc.use_autolayout:
        attrs["useAutolayout"] = doc.use_autolayout
    if doc.use_trait_collections:
        attrs["useTraitCollections"] = doc.use_trait_collections
    if doc.use_safe_areas:
        attrs["useSafeAreas"] = doc.use_safe_areas
    if doc.color_matched:
        attrs["colorMatched"] = doc.color_matched
    if doc.initial_view_controller:
        attrs["initialViewController"] = doc.initial_view_controller
    # additional arbitrary attributes (root)
    for k, v in doc.root_attributes.items():
        if k not in attrs:
            attrs[k] = v
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    head += "<!DOCTYPE document ["
    head += "  <!ENTITY nbsp \"&#160;\">"
    head += "  <!ENTITY bull \"&#8226;\">"
    head += "  <!ENTITY euro \"&#8364;\">"
    head += "]>\n"
    head += _xml_open_tag("document", attrs)
    body = ""
    if doc.device:
        body += _xml_self_tag("device", doc.device)
    if doc.dependencies or doc.plug_ins or doc.capabilities:
        body += "<dependencies>\n"
        for p in doc.plug_ins:
            body += _xml_self_tag("plugIn", p.attributes)
        for c in doc.capabilities:
            body += _xml_self_tag("capability", c.attributes)
        for d in doc.dependencies:
            body += _element_to_xml(d)
        body += "</dependencies>\n"
    if doc.objects:
        body += "<objects>\n"
        for o in doc.objects:
            body += _xibobject_to_xml(o, depth=1)
        body += "</objects>\n"
    if doc.connections:
        body += "<connections>\n"
        for c in doc.connections:
            cattrs = {"source": c.source_id, "destination": c.destination_id,
                     "label": c.label}
            if c.type != "outlet":
                cattrs["type"] = c.type
            body += "    " + _xml_self_tag("connection", cattrs) + "\n"
        body += "</connections>\n"
    if doc.scenes:
        body += "<scenes>\n"
        for s in doc.scenes:
            body += _scene_to_xml(s, depth=1)
        body += "</scenes>\n"
    foot = "</document>\n"
    return head + body + foot


def _xml_open_tag(tag: str, attrs: Dict[str, str]) -> str:
    s = "<" + tag
    for k, v in attrs.items():
        s += ' %s="%s"' % (k, _xml_escape_attr(v))
    s += ">\n"
    return s


def _xml_self_tag(tag: str, attrs: Dict[str, str]) -> str:
    s = "<" + tag
    for k, v in attrs.items():
        s += ' %s="%s"' % (k, _xml_escape_attr(v))
    s += "/>\n"
    return s


def _xml_escape_attr(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def _xibobject_to_xml(o: XIBObject, depth: int = 0) -> str:
    indent = "    " * depth
    head = indent + "<" + o.tag
    for k, v in o.attributes.items():
        head += ' %s="%s"' % (k, _xml_escape_attr(v))
    if not o.children and o.text is None:
        return head + "/>\n"
    head += ">"
    if o.text is not None:
        head += _xml_escape_attr(o.text)
        head += "</" + o.tag + ">\n"
        return head
    head += "\n"
    for c in o.children:
        head += _element_to_xml(c, depth + 1)
    head += indent + "</" + o.tag + ">\n"
    return head


def _element_to_xml(e: XIBElement, depth: int = 0) -> str:
    indent = "    " * depth
    head = indent + "<" + e.tag
    for k, v in e.attributes.items():
        head += ' %s="%s"' % (k, _xml_escape_attr(v))
    if not e.children and e.text is None:
        return head + "/>\n"
    head += ">"
    if e.text is not None:
        head += _xml_escape_attr(e.text)
        head += "</" + e.tag + ">\n"
        return head
    head += "\n"
    for c in e.children:
        head += _element_to_xml(c, depth + 1)
    head += indent + "</" + e.tag + ">\n"
    return head


def _scene_to_xml(s: XIBScene, depth: int = 0) -> str:
    indent = "    " * depth
    head = indent + "<scene"
    for k, v in s.attributes.items():
        head += ' %s="%s"' % (k, _xml_escape_attr(v))
    head += "><objects>\n"
    for o in s.objects:
        head += _xibobject_to_xml(o, depth + 1)
    head += "</objects></scene>\n"
    return head
