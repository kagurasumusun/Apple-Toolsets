"""
ibtool の --output-format 系: xib を plist 形式にダンプする
"""

import plistlib
from io import BytesIO
from typing import List, Tuple, Any, Dict
from .xibdoc import XIBDocument, XIBObject, XIBElement
from .nibcompile import XIB_TAG_TO_CLASS


def dump_objects(doc: XIBDocument) -> Dict[str, Any]:
    """--objects: {com.apple.ibtool.document.objects: {id: {attributes}}}

    Apple ibtool 出力に合わせる:
      - 公開 xib の <objects> 内の全要素 (placeholder, view 等) を出力
      - 子要素 (<viewLayoutGuide>, <color>, <rect> 等) も id があれば出力
      - <connections> 内の <outlet> / <action> は接続情報なので、ここでは出力しない
    """
    out: Dict[str, Any] = {}
    # 公開 objects
    for o in doc.objects:
        attrs = dict(o.attributes)
        attrs["class"] = attrs.get("customClass") or o.tag
        out[o.id] = attrs
        # 子要素 (id 付き) も再帰的に収集
        for c in o.children:
            _collect_object_attrs(c, out)
    return {"com.apple.ibtool.document.objects": out}


def _collect_object_attrs(e, out: Dict[str, Any], depth: int = 0):
    """子要素 (id 付き) を再帰的に out に追加"""
    if depth > 5:  # 循環防止
        return
    if isinstance(e, XIBObject):
        eid = e.id
        if eid and eid not in out:
            attrs = dict(e.attributes)
            attrs["class"] = attrs.get("customClass") or e.tag
            out[eid] = attrs
            for c in e.children:
                _collect_object_attrs(c, out, depth + 1)
    elif hasattr(e, "attributes"):
        eid = e.attributes.get("id")
        if eid and eid not in out:
            attrs = dict(e.attributes)
            # 子要素が id 付きなら object として記録
            if e.tag in ("viewLayoutGuide", "color", "font", "image", "string", "data",
                         "array", "number", "value", "rect", "size", "point"):
                attrs["class"] = e.tag
                out[eid] = attrs
            for c in e.children:
                _collect_object_attrs(c, out, depth + 1)


def _all_objects(doc: XIBDocument):
    """doc.objects + doc.scenes[].objects を結合した iterator"""
    for o in doc.objects:
        yield o
    for s in doc.scenes:
        for o in s.objects:
            yield o


def dump_hierarchy(doc: XIBDocument) -> Dict[str, Any]:
    """--hierarchy: {com.apple.ibtool.document.hierarchy: [ {object-id, label, name?, custom-class?, children?} ]}

    Apple 出力仕様 (実機検証済み):
      - placeholder (IBFilesOwner / IBFirstResponder):
        - label = "File's Owner" / "First Responder" (placeholderIdentifier 由来)
        - name = label (placeholder のみ)
        - customClass が有る場合のみ custom-class キー
      - 通常の object:
        - label = クラス名の human-readable (例: "View", "Safe Area", "Button")
        - name キー無し
        - customClass が有る場合のみ custom-class キー
      - children キーは subview を持つ object のみ
    """
    all_objs = list(_all_objects(doc))
    id_set = {o.id for o in all_objs}
    parent_map: Dict[str, str] = {}
    for o in all_objs:
        for c in o.children:
            cid = c.attributes.get("id")
            if cid:
                parent_map[cid] = o.id

    # クラス名 → human-readable label マッピング
    CLASS_LABEL = {
        "view": "View",
        "viewController": "View Controller",
        "placeholder": None,  # placeholder は placeholderIdentifier から
        "button": "Button",
        "label": "Label",
        "imageView": "Image View",
        "textField": "Text Field",
        "textView": "Text View",
        "stackView": "Stack View",
        "scrollView": "Scroll View",
        "tableView": "Table View",
        "collectionView": "Collection View",
        "tabBarController": "Tab Bar Controller",
        "navigationController": "Navigation Controller",
        "viewLayoutGuide": "Layout Guide",
        "layoutGuide": "Layout Guide",
    }
    # Apple の system layout guide 名
    SYSTEM_LABEL = {
        "viewLayoutGuide": "Safe Area",  # safe area layout guide
    }

    def build_subtree(oid: str) -> Dict[str, Any]:
        # 全体から検索 (doc.objects + scenes[].objects)
        obj = None
        for o in all_objs:
            if o.id == oid:
                obj = o
                break
        if not obj:
            return {}
        attrs = obj.attributes
        is_placeholder = (obj.tag == "placeholder")
        cc = attrs.get("customClass")
        proxied = attrs.get("placeholderIdentifier", "")

        d: Dict[str, Any] = {"object-id": obj.id}

        # label
        if "userLabel" in attrs:
            d["label"] = attrs["userLabel"]
        elif is_placeholder:
            # placeholderIdentifier → label
            if proxied == "IBFilesOwner":
                d["label"] = "File's Owner"
            elif proxied == "IBFirstResponder":
                d["label"] = "First Responder"
            else:
                d["label"] = proxied or "Placeholder"
        else:
            # Class default name
            d["label"] = CLASS_LABEL.get(obj.tag) or cc or obj.tag

        # placeholder のみ name キー
        if is_placeholder and "userLabel" in attrs:
            d["name"] = attrs["userLabel"]
        # customClass が有る場合のみ custom-class
        if cc:
            d["custom-class"] = cc

        # children
        children = []
        for c in obj.children:
            cid = c.attributes.get("id")
            if cid and cid in id_set:
                sub = build_subtree(cid)
                if sub:
                    children.append(sub)
            elif cid and cid not in id_set:
                # child が standalone guide (objects に無いが子として存在)
                sub = {
                    "object-id": cid,
                    "label": _guide_label(c),
                }
                children.append(sub)
        if children:
            d["children"] = children
        return d

    roots = [o for o in all_objs if o.id not in parent_map]
    hier = [build_subtree(o.id) for o in roots if build_subtree(o.id)]
    # Apple 仕様: 公開 objects 全部を root に含める
    # 親が all_objs に無い standalone な子 (例: viewLayoutGuide) は
    # 既に hier に含まれているが、parent_map に含まれていないため
    # ここでも再度追加する必要なし
    return {"com.apple.ibtool.document.hierarchy": hier}


def _guide_label(c: XIBElement) -> str:
    """layout guide / standalone element の human label"""
    if c.tag == "viewLayoutGuide":
        if c.attributes.get("key") == "safeArea":
            return "Safe Area"
        if c.attributes.get("systemType") == "1":
            return "Safe Area"
        return "Layout Guide"
    return c.tag


def dump_connections(doc: XIBDocument) -> Dict[str, Any]:
    """--connections: {com.apple.ibtool.document.connections: {id: {...}}}

    Apple ibtool 出力の接続タイプ:
      - "IBCocoaTouchOutletConnection" (UIKit outlet)
      - "IBCocoaTouchActionConnection" (UIKit action)
      - "IBCocoaTouchEventConnection" (event)
      - "IBSegueConnection" (storyboard segue)
      - "IBBindingConnection" (Cocoa binding)
    Apple の出力 key は:
      - destination-id (object id)
      - destination-label (object label)
      - label (outlet property / action selector / segue identifier)
      - source-id (object id)
      - source-label (object label)
      - type (connection type)
    接続の id は outlet/action/segue 自体の id 属性 (Apple は "sfx-zR-JGt" 形式)
    """
    out: Dict[str, Dict[str, Any]] = {}

    # Apple 接続タイプのマッピング
    TYPE_MAP = {
        "outlet": "IBCocoaTouchOutletConnection",
        "action": "IBCocoaTouchActionConnection",
        "segue": "IBSegueConnection",
    }

    # xib 内 <connections> トップレベル (storyboard)
    for c in doc.connections:
        src = doc.find_object(c.source_id)
        dst = doc.find_object(c.destination_id)
        cid = c.label or c.id or f"CONN_{len(out)+1}"
        out[cid] = {
            "destination-id": c.destination_id,
            "destination-label": dst.attributes.get("userLabel", dst.tag) if dst else "",
            "label": c.label,
            "source-id": c.source_id,
            "source-label": src.attributes.get("userLabel", src.tag) if src else "",
            "type": "IBSegueConnection",
        }

    # xib 内 objects/<obj>/<connections> の outlet / action
    for o in doc.objects:
        for c in o.children:
            if c.tag == "connections":
                for conn in c.children:
                    if conn.tag in ("outlet", "action"):
                        src = doc.find_object(o.id)
                        dst = doc.find_object(conn.attributes.get("destination", ""))
                        cid = conn.attributes.get("id", f"CONN_{len(out)+1}")
                        if conn.tag == "outlet":
                            label = conn.attributes.get("property", "")
                            ctype = "IBCocoaTouchOutletConnection"
                        else:
                            label = conn.attributes.get("selector", "")
                            ctype = "IBCocoaTouchActionConnection"
                        out[cid] = {
                            "destination-id": conn.attributes.get("destination", ""),
                            "destination-label": dst.attributes.get("userLabel", dst.tag) if dst else "",
                            "label": label,
                            "source-id": o.id,
                            "source-label": src.attributes.get("userLabel", src.tag) if src else "",
                            "type": ctype,
                        }
                    elif conn.tag == "segue":
                        cid = conn.attributes.get("id", f"CONN_{len(out)+1}")
                        out[cid] = {
                            "destination-id": conn.attributes.get("destination", ""),
                            "destination-label": "",
                            "label": conn.attributes.get("identifier", ""),
                            "source-id": o.id,
                            "source-label": "",
                            "type": "IBSegueConnection",
                        }
    return {"com.apple.ibtool.document.connections": out}


def dump_classes(doc: XIBDocument) -> Dict[str, Any]:
    """--classes: {com.apple.ibtool.document.classes: {class: {actions, outlets, superclass, class}}}

    Apple ibtool の出力:
      - actions / outlets は {name: type} の dict 形式 (type は "id" 固定でも OK)
      - Apple は actions/outlets を空 dict {} でも常に出力する
      - NSObject は superclass=null
      - 公開 xib 内の class と Apple 内部 built-in class DB をマージして出力

    本実装では:
      1. 公開 xib 内の class を collected
      2. Apple 内部 DB (classes_db.APPLE_CLASSES_DB) とマージ
      3. Apple のキー順 (alphabetical) で出力
    """
    classes: Dict[str, Any] = {}

    # Apple 内部 DB をまずロード
    from .classes_db import APPLE_CLASSES_DB
    for cname, info in APPLE_CLASSES_DB.items():
        classes[cname] = dict(info)

    # xib 内の class を抽出してマージ (xib の方が優先)
    xib_classes = {}
    for o in doc.objects:
        cls = o.attributes.get("customClass") or o.tag
        # xib tag (lowercase) は class として登録しない (Apple 出力は camelCase class 名のみ)
        if cls == o.tag and cls.lower() == cls:
            cls = XIB_TAG_TO_CLASS.get(cls, cls)
        # placeholder (UIProxyObject) は Apple 出力に含めない
        if cls == "UIProxyObject":
            continue
        if cls in xib_classes:
            continue
        actions_list: List[str] = []
        outlets_list: List[str] = []
        def walk(e):
            if e.tag == "outlet":
                outlets_list.append(e.attributes.get("property", ""))
            elif e.tag == "action":
                actions_list.append(e.attributes.get("selector", ""))
            for c in e.children:
                walk(c)
        for c in o.children:
            walk(c)
        actions_d = {a: "id" for a in actions_list}
        outlets_d = {o: "id" for o in outlets_list}
        # Apple 内部 DB にあるならそれを使う、なければ新規作成
        if cls in classes:
            entry = classes[cls]
            # xib 内に outlet/action があれば追加
            for o_name in outlets_list:
                if "outlets" not in entry:
                    entry["outlets"] = {}
                entry["outlets"][o_name] = "id"
            for a_name in actions_list:
                if "actions" not in entry:
                    entry["actions"] = {}
                entry["actions"][a_name] = "id"
        else:
            # 新規
            superclass = "NSObject"
            if cls == "UIView":
                superclass = "UIResponder"
            elif cls == "UIViewController":
                superclass = "UIResponder"
            elif cls == "UIResponder":
                superclass = "NSObject"
            elif cls.startswith("UI"):
                superclass = "NSObject"
            entry = {
                "class": cls,
                "superclass": superclass,
                "actions": actions_d,
                "outlets": outlets_d,
            }
        xib_classes[cls] = entry

    # xib 内の class を上書き (Apple DB にあっても xib の値で更新)
    for cname, entry in xib_classes.items():
        classes[cname] = entry

    # Apple の出力順に揃える (alphabetical)
    classes = {k: classes[k] for k in sorted(classes.keys())}
    return {"com.apple.ibtool.document.classes": classes}


def dump_version_history(doc: XIBDocument) -> Dict[str, Any]:
    """--version-history: {com.apple.ibtool.document.version-history: {interface-builder-version: ...}}

    Apple 出力: {"interface-builder-version": {"com.apple.InterfaceBuilderKit": "22154"}}
    """
    return {
        "com.apple.ibtool.document.version-history": {
            "interface-builder-version": {
                "com.apple.InterfaceBuilderKit": doc.tools_version,
            }
        }
    }


def dump_localizable_strings(doc: XIBDocument) -> Dict[str, Any]:
    """--localizable-strings: xib 内 localizable 文字列 (title / text / placeholder / prompt 等)"""
    out: Dict[str, Dict[str, str]] = {}
    for o in doc.objects:
        for e in _walk_elements(o):
            for key in ("title", "text", "placeholder", "prompt", "label", "hint",
                       "accessibilityLabel", "accessibilityHint", "minValue", "maxValue"):
                if key in e.attributes:
                    v = e.attributes[key]
                    if v and v.strip():
                        out.setdefault(o.id, {})[key] = v
    return {"com.apple.ibtool.document.localizable-strings": out}


def dump_localizable_geometry(doc: XIBDocument) -> Dict[str, Any]:
    """--localizable-geometry: Apple 出力 8 フィールド (frameOrigin, frameSize, autoresizingMask, ...)"""
    return {"com.apple.ibtool.document.localizable-geometry": _geometry_props(doc)}


def dump_localizable_stringarrays(doc: XIBDocument) -> Dict[str, Any]:
    """--localizable-stringarrays: 配列 localizable (現状未対応 → 空 dict)"""
    return {"com.apple.ibtool.document.localizable-stringarrays": {}}


def dump_localizable_other(doc: XIBDocument) -> Dict[str, Any]:
    """--localizable-other: その他の localizable (現状未対応 → 空 dict)"""
    return {"com.apple.ibtool.document.localizable-other": {}}


def dump_localizable_to_many_relationships(doc: XIBDocument) -> Dict[str, Any]:
    """--localizable-to-many-relationships: to-many 関係 (現状未対応 → 空 dict)"""
    return {"com.apple.ibtool.document.localizable-to-many-relationships": {}}


def dump_localizable_all(doc: XIBDocument) -> Dict[str, Any]:
    """--localizable-all: 全 localizable = geometry 相当 (Apple 出力に一致)

    Apple の出力 (実機検証済み) では:
      - --localizable-all も --localizable-geometry と同じ 8 フィールド
      - UIView / UILayoutGuide / etc の frame / autoresizingMask / priority 系
    """
    return {"com.apple.ibtool.document.localizable-all": _geometry_props(doc)}


def _geometry_props(doc: XIBDocument) -> Dict[str, Dict[str, Any]]:
    """8 種類の geometry プロパティ抽出

    Apple ibtool 出力キー:
      - frameOrigin: "{x, y}" 形式 (str)
      - frameSize: "{w, h}" 形式 (str)
      - ibDesignAutoresizingMask: int
      - ibExternalExplicitTranslatesAutoresizingMask: bool
      - ibShadowedHorizontalContentCompressionResistancePriority: real
      - ibShadowedHorizontalContentHuggingPriority: real
      - ibShadowedVerticalContentCompressionResistancePriority: real
      - ibShadowedVerticalContentHuggingPriority: real
    """
    out: Dict[str, Dict[str, Any]] = {}
    for o in doc.objects:
        attrs = o.attributes
        rect = _parse_rect(attrs.get("frame", ""))
        if rect is None:
            # children の <rect> から取得
            for c in o.children:
                if c.tag == "rect" and c.attributes.get("key") == "frame":
                    rect = _parse_rect_from_rect(c.attributes)
                    break
        if rect is None:
            continue
        # Apple 仕様 key 順: frameOrigin, frameSize, ibDesignAutoresizingMask,
        # ibExternalExplicitTranslatesAutoresizingMaskIntoConstraints,
        # ibShadowed{4 priorities}
        d: Dict[str, Any] = {}
        d["frameOrigin"] = "{%g, %g}" % (rect[0], rect[1])
        d["frameSize"] = "{%g, %g}" % (rect[2], rect[3])
        # autoresizingMask (Apple 仕様: widthSizable+heightSizable = 18 のような bitmask)
        am = attrs.get("autoresizingMask")
        if am:
            d["ibDesignAutoresizingMask"] = _parse_autoresizing_mask(am)
        else:
            # children の <autoresizingMask> から取得
            for c in o.children:
                if c.tag == "autoresizingMask":
                    d["ibDesignAutoresizingMask"] = _parse_autoresizing_mask_from_child(c)
                    break
            else:
                d["ibDesignAutoresizingMask"] = 0
        # translatesAutoresizingMaskIntoConstraints
        t = attrs.get("translatesAutoresizingMaskIntoConstraints", "").upper() == "NO"
        d["ibExternalExplicitTranslatesAutoresizingMaskIntoConstraints"] = not t
        # priorities
        d["ibShadowedHorizontalContentCompressionResistancePriority"] = 750.0
        d["ibShadowedHorizontalContentHuggingPriority"] = 250.0
        d["ibShadowedVerticalContentCompressionResistancePriority"] = 750.0
        d["ibShadowedVerticalContentHuggingPriority"] = 250.0
        out[o.id] = d
    return out


def _parse_rect(s: str):
    """frame string "{{x, y}, {w, h}}" をパース"""
    if not s:
        return None
    s = s.strip()
    if s.startswith("{{") and s.endswith("}}"):
        s = s[1:-1]
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
    parts = s.split("}, {") if "}, {" in s else s.split(", ")
    try:
        if len(parts) == 4:
            return tuple(float(p) for p in parts)
        if len(parts) == 2:
            return (0.0, 0.0, float(parts[0]), float(parts[1]))
    except Exception:
        return None
    return None


def _parse_rect_from_rect(attrs: dict):
    """<rect key="frame" x="..." y="..." width="..." height="..."/> からパース"""
    try:
        return (float(attrs.get("x", 0)), float(attrs.get("y", 0)),
                float(attrs.get("width", 0)), float(attrs.get("height", 0)))
    except Exception:
        return None


def _parse_autoresizing_mask(s: str) -> int:
    """autoresizingMask string → int

    Apple の出力は int (bitfield):
      0=none, 18=full (widthSizable+heightSizable+flexibleMargins = 0x12)
    16 = widthSizable
    8 = heightSizable
    5 = right+top margins
    等
    実際のフラグ:
      UIViewAutoresizingNone = 0
      UIViewAutoresizingFlexibleLeftMargin = 1
      UIViewAutoresizingFlexibleWidth = 2
      UIViewAutoresizingFlexibleRightMargin = 4
      UIViewAutoresizingFlexibleTopMargin = 8
      UIViewAutoresizingFlexibleHeight = 16
      UIViewAutoresizingFlexibleBottomMargin = 32
    widthSizable+heightSizable = 2+16 = 18
    """
    flags = 0
    s = s.upper()
    if "WIDTHSIZABLE" in s:
        flags |= 2
    if "HEIGHTSIZABLE" in s:
        flags |= 16
    if "FLEXIBLELEFTMARGIN" in s:
        flags |= 1
    if "FLEXIBLERIGHTMARGIN" in s:
        flags |= 4
    if "FLEXIBLETOPMARGIN" in s:
        flags |= 8
    if "FLEXIBLEBOTTOMMARGIN" in s:
        flags |= 32
    return flags


def _parse_autoresizing_mask_from_child(c: XIBElement) -> int:
    """<autoresizingMask widthSizable="YES" heightSizable="YES"/> から int を計算"""
    flags = 0
    a = c.attributes
    if a.get("widthSizable", "").upper() == "YES":
        flags |= 2
    if a.get("heightSizable", "").upper() == "YES":
        flags |= 16
    if a.get("flexibleMinX", "").upper() == "YES" or a.get("flexibleLeftMargin", "").upper() == "YES":
        flags |= 1
    if a.get("flexibleMaxX", "").upper() == "YES" or a.get("flexibleRightMargin", "").upper() == "YES":
        flags |= 4
    if a.get("flexibleMinY", "").upper() == "YES" or a.get("flexibleTopMargin", "").upper() == "YES":
        flags |= 8
    if a.get("flexibleMaxY", "").upper() == "YES" or a.get("flexibleBottomMargin", "").upper() == "YES":
        flags |= 32
    return flags


def _walk_elements(o: XIBObject):
    """XIBObject とその子を全部 yield するヘルパ"""
    yield o
    for c in o.children:
        yield c
        for sub in _walk_elements_children(c):
            yield sub


def _walk_elements_children(e):
    yield e
    for c in e.children:
        yield from _walk_elements_children(c)


def dump_all(doc: XIBDocument) -> Dict[str, Any]:
    """--all: Apple ibtool 互換キー順序
    Apple 出力のキー順 (実機検証済み):
      1. com.apple.ibtool.document.classes
      2. com.apple.ibtool.document.connections
      3. com.apple.ibtool.document.errors
      4. com.apple.ibtool.document.hierarchy
      5. com.apple.ibtool.document.localizable-all
      6. com.apple.ibtool.document.notices
      7. com.apple.ibtool.document.objects
      8. com.apple.ibtool.document.version-history
      9. com.apple.ibtool.document.warnings
    """
    d: Dict[str, Any] = {}
    d["com.apple.ibtool.document.classes"] = dump_classes(doc)["com.apple.ibtool.document.classes"]
    d["com.apple.ibtool.document.connections"] = dump_connections(doc)["com.apple.ibtool.document.connections"]
    d["com.apple.ibtool.document.errors"] = find_errors(doc)
    d["com.apple.ibtool.document.hierarchy"] = dump_hierarchy(doc)["com.apple.ibtool.document.hierarchy"]
    d["com.apple.ibtool.document.localizable-all"] = dump_localizable_all(doc)["com.apple.ibtool.document.localizable-all"]
    d["com.apple.ibtool.document.notices"] = find_notices(doc)
    d["com.apple.ibtool.document.objects"] = dump_objects(doc)["com.apple.ibtool.document.objects"]
    d["com.apple.ibtool.document.version-history"] = dump_version_history(doc)["com.apple.ibtool.document.version-history"]
    d["com.apple.ibtool.document.warnings"] = find_warnings(doc)
    return d


# Errors/warnings/notices - Apple ibtool は xib 内の特定の条件で出力する
# 完全再現は不可能なので、xib 内の問題パターンをヒューリスティックに検出する
# Apple の出力形式: 項目は dict (空なら {}、非空なら {key: {message, type}})
def find_warnings(doc: XIBDocument) -> Dict[str, Any]:
    """--warnings: Apple 互換 dict 形式

    Apple の出力は通常 {} (空 dict)。pyibtool も空 dict を返す。
    (孤立 object 検出は Apple 内部ヒューリスティックで完全再現不可)
    """
    return {}


def find_errors(doc: XIBDocument) -> Dict[str, Any]:
    """--errors: Apple 互換 dict 形式 (空 dict)"""
    return {}


def find_notices(doc: XIBDocument) -> Dict[str, Any]:
    """--notices: Apple 互換 dict 形式 (空 dict)"""
    return {}


def plist_to_bytes(d: Any, fmt: str = "xml1") -> bytes:
    """dict を指定フォーマット (xml1 / binary1 / human-readable-text) の plist バイト列に"""
    if fmt in ("xml1", "xml"):
        return plistlib.dumps(d, fmt=plistlib.FMT_XML)
    elif fmt in ("binary1", "binary"):
        return plistlib.dumps(d, fmt=plistlib.FMT_BINARY)
    elif fmt in ("human-readable-text", "human"):
        return human_readable_plist(d).encode("utf-8")
    else:
        raise ValueError("unknown output format: %s" % fmt)


def human_readable_plist(obj, indent=0) -> str:
    """Apple 風の human-readable plist テキスト表現"""
    pad = "    " * indent
    if isinstance(obj, dict):
        lines = ["{", ]
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append("%s    %s = %s" % (pad, k, human_readable_plist(v, indent + 1)))
            else:
                lines.append("%s    %s = %s;" % (pad, k, _hr_value(v)))
        lines.append("%s}" % pad)
        return "\n".join(lines)
    elif isinstance(obj, list):
        lines = ["("]
        for v in obj:
            if isinstance(v, (dict, list)):
                lines.append("%s    %s," % (pad, human_readable_plist(v, indent + 1)))
            else:
                lines.append("%s    %s," % (pad, _hr_value(v)))
        lines.append("%s)" % pad)
        return "\n".join(lines)
    else:
        return _hr_value(obj)


def _hr_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, bytes):
        return "<" + v.hex() + ">"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return repr(v)
