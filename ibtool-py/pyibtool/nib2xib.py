"""
NIB (NIBArchive) → xib (XML plist) 変換

NIBArchive の object/value/class/key を解析して、
意味的に xib ドキュメントに戻す。

これは Apple 純正 ibtool には無い機能で、pyibtool の独自機能。
xib 形式は Apple 内部の IB 表現で、NIBArchive 形式は runtime バイナリ。
両者は異なるため、変換は「近似」となり、情報を一部失う可能性がある。
"""

from typing import List, Dict, Any, Optional, Tuple

from .xibdoc import (
    XIBDocument, XIBObject, XIBElement, XIBConnection,
    parse_xib_text, serialize_xib,
)
from .nibarchive import NIBArchive, Object, CoderValue, Key, ClassName


# Foundation Collection の特殊キー
NSINLINED_VALUE = "NSInlinedValue"
UINIB_EMPTY_KEY = "UINibEncoderEmptyKey"


# Class 名の → customClass への変換
def class_name_to_xib_tag(class_name: str) -> str:
    """NIB class name → xib tag のベストエフォート変換

    注意: 既知の Apple class は標準 xib tag に変換。
    未知の custom class (HSChooserWindow 等) は "customView" 等にフォールバック
    し、customClass 属性でクラス名を保持する。
    """
    # 既知の Cocoa / CocoaTouch class
    known = {
        "NSObject": "object",
        "NSArray": "array",
        "NSDictionary": "dictionary",
        "NSString": "string",
        "NSData": "data",
        "NSValue": "value",
        "NSNumber": "number",
        "UIProxyObject": "placeholder",
        "UIView": "view",
        "NSView": "view",  # Cocoa NSView → view (macOS xib)
        "NSWindow": "window",
        "NSApplication": "application",
        "NSMenu": "menu",
        "NSMenuItem": "menuItem",
        "NSControl": "control",
        "NSTextField": "textField",
        "NSButton": "button",
        "NSImageView": "imageView",
        "NSWindowController": "windowController",
        "NSViewController": "viewController",
        "UIColor": "color",
        "UIFont": "font",
        "UIImage": "image",
        "NSColor": "color",
        "NSFont": "font",
        "NSImage": "image",
        "UILayoutGuide": "layoutGuide",
        "UIRuntimeOutletConnection": "outlet",  # → 個別の UIRuntimeOutletConnection として
        "UIRuntimeActionConnection": "action",
        # UIKit
        "UIButton": "button",
        "UILabel": "label",
        "UIImageView": "imageView",
        "UITextField": "textField",
        "UITextView": "textView",
        "UIStackView": "stackView",
        "UIScrollView": "scrollView",
        "UITableView": "tableView",
        "UICollectionView": "collectionView",
        "UIProgressView": "progressView",
        "UIActivityIndicatorView": "activityIndicatorView",
        "UISegmentedControl": "segmentedControl",
        "UISlider": "slider",
        "UIStepper": "stepper",
        "UISwitch": "switch",
        "UIDatePicker": "datePicker",
        "UIPickerView": "pickerView",
        "MKMapView": "mapView",
        "WKWebView": "webView",
        "UISearchBar": "searchBar",
        "UIToolbar": "toolbar",
        "UINavigationBar": "navigationBar",
        "UITabBar": "tabBar",
        "UINavigationItem": "navigationItem",
        "UIBarButtonItem": "barButtonItem",
        "UIViewController": "viewController",
        "UITableViewController": "tableViewController",
        "UICollectionViewController": "collectionViewController",
        "UINavigationController": "navigationController",
        "UITabBarController": "tabBarController",
        "UISplitViewController": "splitViewController",
        "UIPageViewController": "pageViewController",
    }
    if class_name in known:
        return known[class_name]
    # 未知の class (HSChooserWindow 等) は customView にフォールバック
    # 呼び出し側で customClass 属性を設定する
    return "customView"


def nib2xib(arch: NIBArchive, doc_type: str = "com.apple.InterfaceBuilder3.CocoaTouch.XIB",
            target_runtime: str = "iOS.CocoaTouch") -> XIBDocument:
    """NIBArchive → XIBDocument 変換"""
    doc = XIBDocument(
        doc_type=doc_type,
        target_runtime=target_runtime,
        tools_version="26000",
    )

    # Class index → tag
    class_to_tag = {}
    for cn in arch.class_names:
        class_to_tag[cn.name] = class_name_to_xib_tag(cn.name)

    # 1. Object ごとに xib object を作る
    obj_to_xib_obj: Dict[int, XIBObject] = {}
    for i, obj in enumerate(arch.objects):
        cname = arch.lookup_class(obj.class_index)
        tag = class_to_tag.get(cname, "object")
        attrs = {"id": f"obj-{i}"}
        # NSObject / NSArray / NSString / Foundation 系は customClass を付けない
        if cname and cname not in ("NSObject", "NSArray", "NSString", "UIColor",
                                    "UIFont", "UIImage", "NSColor", "UILayoutGuide",
                                    "NSView", "NSWindow", "NSApplication", "NSMenu",
                                    "NSMenuItem", "NSControl",
                                    "UIRuntimeOutletConnection",
                                    "UIRuntimeActionConnection"):
            # HSChooserWindow のような custom class は tag を標準 tag に + customClass で表現
            # ただし class_name_to_xib_tag がそのまま返した = 既知のクラス
            # 例: UIButton → button タグ + customClass=UIButton (本来は不要)
            # ここでは class 名が標準クラス名と同じなら customClass スキップ
            if cname not in ("UIView", "UIButton", "UILabel", "UIImageView",
                             "UITextField", "UITextView", "UIStackView",
                             "UIScrollView", "UITableView", "UICollectionView",
                             "UIProgressView", "UIActivityIndicatorView",
                             "UISegmentedControl", "UISlider", "UIStepper",
                             "UISwitch", "UIDatePicker", "UIPickerView",
                             "MKMapView", "WKWebView", "UISearchBar",
                             "UIToolbar", "UINavigationBar", "UITabBar",
                             "UINavigationItem", "UIBarButtonItem"):
                attrs["customClass"] = cname
        if cname == "UIProxyObject":
            # UIProxyObject の NSString (UIProxiedObjectIdentifier) を見て
            # File's Owner / First Responder を判定
            proxy_id = ""
            for j in range(obj.value_start, obj.value_start + obj.value_count):
                if j >= len(arch.values):
                    break
                v = arch.values[j]
                key = arch.lookup_key(v.key_index)
                if key == "UIProxiedObjectIdentifier" and v.is_objref:
                    target_idx = v.objref_index
                    if 0 <= target_idx < len(arch.objects):
                        target_obj = arch.objects[target_idx]
                        for k in range(target_obj.value_start,
                                       target_obj.value_start + target_obj.value_count):
                            if k >= len(arch.values):
                                break
                            tv = arch.values[k]
                            tkey = arch.lookup_key(tv.key_index)
                            if tkey == "NS.bytes" and tv.type == 8 and tv.data:
                                proxy_id = tv.data.decode("utf-8", errors="replace")
                                break
                    break
            if proxy_id == "IBFilesOwner":
                attrs["placeholderIdentifier"] = "IBFilesOwner"
                attrs["userLabel"] = "File's Owner"
                attrs["sceneMemberID"] = "filesOwner"
            elif proxy_id == "IBFirstResponder":
                attrs["placeholderIdentifier"] = "IBFirstResponder"
                attrs["customClass"] = "UIResponder"
                attrs["sceneMemberID"] = "firstResponder"
            else:
                attrs["placeholderIdentifier"] = "IBFilesOwner"
                attrs["userLabel"] = cname
        xib_obj = XIBObject(id=attrs["id"], tag=tag, attributes=attrs)
        obj_to_xib_obj[i] = xib_obj

    # 1b. UIProxyObject の UIProxiedObjectIdentifier が指す NSString が
    # 独立 object として xib に存在するかを確認し、無ければ追加する
    # 存在する場合は placeholder に UIProxiedObjectIdentifier 属性を設定
    proxy_string_indices: Dict[int, int] = {}  # placeholder_obj_idx → string_obj_idx
    for i, obj in enumerate(arch.objects):
        cname = arch.lookup_class(obj.class_index)
        if cname != "UIProxyObject":
            continue
        for j in range(obj.value_start, obj.value_start + obj.value_count):
            if j >= len(arch.values):
                break
            v = arch.values[j]
            key = arch.lookup_key(v.key_index)
            if key == "UIProxiedObjectIdentifier" and v.is_objref:
                target_idx = v.objref_index
                if 0 <= target_idx < len(arch.objects):
                    target_cname = arch.lookup_class(arch.objects[target_idx].class_index)
                    if target_cname == "NSString":
                        if target_idx not in obj_to_xib_obj:
                            # 独立 object として追加
                            tobj = arch.objects[target_idx]
                            s_attrs = {"id": f"obj-{target_idx}"}
                            for k in range(tobj.value_start,
                                           tobj.value_start + tobj.value_count):
                                if k >= len(arch.values):
                                    break
                                tv = arch.values[k]
                                tkey = arch.lookup_key(tv.key_index)
                                if tkey == "NS.bytes" and tv.type == 8 and tv.data:
                                    s_attrs["NS.bytes"] = tv.data.decode("utf-8", errors="replace")
                                    break
                            obj_to_xib_obj[target_idx] = XIBObject(
                                id=s_attrs["id"], tag="string", attributes=s_attrs
                            )
                            proxy_string_indices[i] = target_idx
                        else:
                            proxy_string_indices[i] = target_idx
                        # placeholder に UIProxiedObjectIdentifier 属性を設定
                        # (nibuild が独立した <string> を参照することを認識する)
                        obj_to_xib_obj[i].attributes["UIProxiedObjectIdentifier"] = \
                            f"obj-{target_idx}"

    # 2. 各 object の value を xib の属性または子要素に変換
    # CGRect / CGSize / CGPoint などの特殊キーは <rect> / <size> / <point> 子要素として出力
    RECT_KEYS = {"UIBounds", "UIOffset", "UIKnob", "UIMinimumSize",
                 "UIPressableKnobMin", "UIPressableKnobMax"}
    SIZE_KEYS = set()
    POINT_KEYS = set()

    def _decode_cg_special(v) -> Optional[str]:
        """data の type=8 で CGRect 等 (先頭 byte 0x07) を <rect> 用に解析"""
        if v.type != 8 or not v.data or len(v.data) < 1:
            return None
        first = v.data[0]
        # Apple の data 形式: 0x07 + 2-4 double (LE)
        if first == 0x07:
            if len(v.data) >= 1 + 8 * 2:
                import struct
                vals = struct.unpack("<dd", v.data[1:1 + 16])
                return ("x", "y", "w", "h")  # type=rect (4 doubles 期待)
        return None

    def _decode_cg_data(v) -> Optional[Tuple[str, list]]:
        """Apple の data (0x07 + doubles) を 4 doubles にデコード"""
        if v.type != 8 or not v.data or len(v.data) < 1:
            return None
        if v.data[0] != 0x07:
            return None
        import struct
        n = (len(v.data) - 1) // 8
        if n not in (2, 3, 4):
            return None
        vals = struct.unpack("<" + "d" * n, v.data[1:1 + 8 * n])
        return ("d%d" % n, list(vals))

    for i, obj in enumerate(arch.objects):
        xib_obj = obj_to_xib_obj[i]
        cname = arch.lookup_class(obj.class_index)
        for j in range(obj.value_start, obj.value_start + obj.value_count):
            if j >= len(arch.values):
                break
            v = arch.values[j]
            key = arch.lookup_key(v.key_index)
            if not key:
                continue
            if key == NSINLINED_VALUE:
                continue
            if key == UINIB_EMPTY_KEY:
                continue
            # $class は XML attribute として書かない (ElementTree が $ で
            # 始まる attribute 名を許可しないため)
            if key == "$class":
                continue
            # $classes, NS.objects, NS.keys も同様
            if key in ("$classes", "NS.objects", "NS.keys"):
                continue

            # UIProxyObject の UIProxiedObjectIdentifier は objref として書く
            # (これが string "IBFilesOwner" の NSString object を指す)
            # → objref 先の NSString が既に独立 object として doc.objects に
            # 存在する場合は何も書かない (nibuild が重複作成しないように)
            if key == "UIProxiedObjectIdentifier" and cname == "UIProxyObject" and v.is_objref:
                # 既に obj-{v.objref_index} が独立 object として存在するかは
                # nib2xib の呼び出し側で別途処理する。
                # ここでは書かない (nibuild が placeholder 用 NSString を
                # 別途作るので二重化する)。
                continue

            # 特殊処理: CGRect 等
            if key in RECT_KEYS and v.type == 8 and v.data:
                # <rect key="frame" x="..." y="..." width="..." height="..."/>
                if v.data[0] == 0x07 and len(v.data) >= 1 + 8 * 4:
                    import struct
                    x, y, w, h = struct.unpack("<dddd", v.data[1:1 + 32])
                    rect_attrs = {"key": key, "x": f"{x}", "y": f"{y}",
                                  "width": f"{w}", "height": f"{h}"}
                    xib_obj.children.append(XIBElement(
                        tag="rect",
                        attributes=rect_attrs,
                    ))
                    continue
            # 数値属性として処理 (key=value 形式)
            # 文字列 / 数値 / bool / nil / objref
            if v.is_objref:
                xib_obj.attributes[key] = f"obj-{v.objref_index}"
            elif v.type == 4:  # true
                xib_obj.attributes[key] = "YES"
            elif v.type == 5:  # false
                xib_obj.attributes[key] = "NO"
            elif v.type == 9:  # nil
                pass
            elif v.type == 8:  # data
                # 文字列として読み込み (空 bytes を含む)
                try:
                    s = v.data.decode("utf-8")
                    # XML コントロール文字を含む場合は破棄
                    if any(ord(c) < 0x20 and c not in "\t\n\r" for c in s):
                        pass
                    else:
                        xib_obj.attributes[key] = s
                except Exception:
                    pass
            elif v.type in (0, 1, 2, 3):  # int
                xib_obj.attributes[key] = str(v.data)
            elif v.type in (6, 7):  # float/double
                xib_obj.attributes[key] = str(v.data)
            else:
                # その他: 文字列化 (bytes なら decode して空文字列に)
                if v.data is not None:
                    if isinstance(v.data, bytes):
                        try:
                            xib_obj.attributes[key] = v.data.decode("utf-8", errors="replace")
                        except Exception:
                            pass
                    else:
                        xib_obj.attributes[key] = str(v.data)

    doc.objects = list(obj_to_xib_obj.values())

    # 3. Connections
    for i, obj in enumerate(arch.objects):
        cname = arch.lookup_class(obj.class_index)
        if cname in ("UIRuntimeOutletConnection", "UIRuntimeActionConnection"):
            src = None
            dst = None
            label = ""
            for j in range(obj.value_start, obj.value_start + obj.value_count):
                if j >= len(arch.values):
                    break
                v = arch.values[j]
                key = arch.lookup_key(v.key_index)
                if key == "UIDestination" and v.is_objref:
                    dst = f"obj-{v.objref_index}"
                elif key == "UISource" and v.is_objref:
                    src = f"obj-{v.objref_index}"
                elif key == "UILabel" and v.is_objref:
                    # UILabel が objref の場合、objref 先の NSString を取得
                    target_idx = v.objref_index
                    if 0 <= target_idx < len(arch.objects):
                        target_obj = arch.objects[target_idx]
                        for k in range(target_obj.value_start,
                                       target_obj.value_start + target_obj.value_count):
                            if k >= len(arch.values):
                                break
                            tv = arch.values[k]
                            tkey = arch.lookup_key(tv.key_index)
                            if tkey == "NS.bytes" and tv.type == 8 and tv.data:
                                label = tv.data.decode("utf-8", errors="replace")
                                break
                elif key == "UILabel":
                    label = v.data.decode("utf-8") if isinstance(v.data, bytes) else str(v.data)
            if src and dst:
                # connection を xib の <connections> として追加
                src_obj = obj_to_xib_obj.get(int(src.split("-")[1])) if src else None
                if src_obj is not None:
                    # 独立した <outlet>/<action> object として作る
                    # (Apple の nib 形式と一致)
                    outlet_attrs = {"id": f"obj-{i}",
                                    "UILabel": label if label else "objref:-1",
                                    "UISource": src,
                                    "UIDestination": dst}
                    if cname == "UIRuntimeOutletConnection":
                        conn_tag = "outlet"
                    else:
                        conn_tag = "action"
                    obj_to_xib_obj[i] = XIBObject(
                        id=f"obj-{i}", tag=conn_tag, attributes=outlet_attrs
                    )

    return doc


if __name__ == "__main__":
    import sys
    from .nibarchive import parse_nib, dump
    for path in sys.argv[1:]:
        with open(path, "rb") as f:
            data = f.read()
        arch = parse_nib(data)
        dump(arch)
        print()
        # nib → xib
        doc = nib2xib(arch)
        out = serialize_xib(doc)
        print("=== xib ===")
        print(out[:2000])
