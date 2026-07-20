"""
xib → NIBArchive (nib) バイナリ生成 (pure Python)

実装方針:
  - ヘッダ (50 バイト) は Archaeology 仕様に従う
  - テーブル 4 種 (objects / keys / values / classNames) を Apple の vint32 形式で書く
  - 値は value type (int/bool/string/double/data/nil/objectref) で encode
  - Foundation Collection (NSArray/NSDictionary) はインライン化

注意:
  - 本実装は「runtime で最低限ロードできる nib」を目指すもの
  - Xcode 26.5 (macOS 26) の nib との完全バイト一致は未検証
  - compressed/encrypted セクションは未対応
"""

import io
import struct
from typing import List

from .xibdoc import XIBDocument, XIBObject, XIBElement
from .nibarchive import (
    T_INT8, T_INT16, T_INT32, T_INT64, T_TRUE, T_FALSE,
    T_FLOAT, T_DOUBLE, T_DATA, T_NIL, T_OBJREF,
    CoderValue, Key, Object, ClassName, NIBArchive,
    write_vint,
)
from typing import Optional


# 既知の NSCoder キー (iOS フレームワークで定義される)
KNOWN_KEYS = {
    "$class", "$classes", "NS.bytes", "NS.objects", "NS.keys",
    "NSInlinedValue", "UINibEncoderEmptyKey",
    "UINibTopLevelObjectsKey", "UINibObjectsKey", "UINibConnectionsKey",
    "UINibVisibleWindowsKey", "UINibAccessibilityConfigurationsKey",
    "UINibKeyValuePairsKey", "UINibTraitStorageListsKey",
    "UINibLNEVersionKey", "UINibObservedPropertiesKey",
    "UIProxiedObjectIdentifier",
    "UIBounds", "UICenter", "UISubviews", "UIAutoresizeSubviews",
    "UIAutoresizingMask", "UIBackgroundColor", "UIOpaque",
    "UIShadowOffset", "UIText", "UITextColor",
    "UIAdjustsFontSizeToFit", "UIFont", "UIContentMode",
    "UIUserInteractionDisabled", "UIViewDoesNotTranslateAutoresizingMaskIntoConstraints",
    "UIViewContentHuggingPriority",
    "UIFontName", "UIFontFamilyName", "UIFontPointSize", "UISystemFont",
    "UIAlpha", "UIRed", "UIGreen", "UIBlue", "NSRGB", "NSColorSpace",
    "UIColorComponentCount", "UIClearsContextBeforeDrawing",
    "UILayoutGuideOwningView", "UIDestination", "UISource",
    "UILayoutGuideIdentifier", "UILayoutGuideAllowsNegativeDimensions",
    "UILayoutGuideOwningViewIsLocked", "UILayoutGuideShouldBeArchived",
    "UIViewSemanticContentAttribute", "UIViewLargeContentStoredProperties",
    "UISystemColorName", "UIDeepDrawRect",
    "UITitle", "UIImage", "UINormalTitle", "UIHighlightedTitle",
    "UINormalImage", "UIHighlightedImage", "UIPressedColor",
    "UIHighlightedColor", "UIDisabledColor", "UISelectedTitle",
    "UIEnabled", "UIHighlighted", "UISelected",
    "UIImageViewImage", "UIUserLabel", "UIName",
    "UIElementIdentifier",
    # macOS 用
    "NSFrameSize", "NSFrameOrigin", "NSSuperview", "NSNextResponder",
    "NSWindow", "NSView", "NSFont", "NSColor", "NSString",
    # NSObject デフォルト
    "hash", "superclass", "description", "debugDescription",
}


# xib 上の属性 → NSCoder キーのマッピング
ATTRIBUTE_TO_KEY = {
    "frame": "UIBounds",
    "bounds": "UIBounds",
    "center": "UICenter",
    "text": "UIText",
    "title": "UITitle",
    "tag": "tag",
    "alpha": "UIAlpha",
    "red": "UIRed",
    "green": "UIGreen",
    "blue": "UIBlue",
    "colorName": "UISystemColorName",
    "fontName": "UIFontName",
    "fontSize": "UIFontPointSize",
    "userLabel": "UIUserLabel",
    "name": "UIName",
    "elementIdentifier": "UIElementIdentifier",
}


# xib の tag → Cocoa class 名のマッピング (iOS 中心)
# Apple の nib では class に厳密な Cocoa クラス名が入る
XIB_TAG_TO_CLASS = {
    # Cocoa Touch (iOS)
    "view": "UIView",
    "placeholder": "UIProxyObject",
    "viewController": "UIViewController",
    "tableViewController": "UITableViewController",
    "collectionViewController": "UICollectionViewController",
    "navigationController": "UINavigationController",
    "tabBarController": "UITabBarController",
    "splitViewController": "UISplitViewController",
    "pageViewController": "UIPageViewController",
    "button": "UIButton",
    "label": "UILabel",
    "imageView": "UIImageView",
    "textField": "UITextField",
    "textView": "UITextView",
    "stackView": "UIStackView",
    "scrollView": "UIScrollView",
    "tableView": "UITableView",
    "collectionView": "UICollectionView",
    "progressView": "UIProgressView",
    "activityIndicatorView": "UIActivityIndicatorView",
    "segmentedControl": "UISegmentedControl",
    "slider": "UISlider",
    "stepper": "UIStepper",
    "switch": "UISwitch",
    "datePicker": "UIDatePicker",
    "pickerView": "UIPickerView",
    "mapView": "MKMapView",
    "webView": "WKWebView",
    "searchBar": "UISearchBar",
    "toolbar": "UIToolbar",
    "navigationBar": "UINavigationBar",
    "tabBar": "UITabBar",
    "navigationItem": "UINavigationItem",
    "barButtonItem": "UIBarButtonItem",
    "layoutGuide": "UILayoutGuide",
    "menu": "UIMenu",
    # Foundation
    "object": "NSObject",
    "array": "NSArray",
    "string": "NSString",
    "data": "NSData",
    "dictionary": "NSDictionary",
    "value": "NSValue",
    "number": "NSNumber",
    "color": "UIColor",
    "font": "UIFont",
    "image": "UIImage",
    "rect": "NSValue",  # CGRect encoded as NSValue
    "size": "NSValue",
    "point": "NSValue",
    # Storyboard
    "scene": "NSObject",
    "segue": "UIStoryboardSegue",
    "connections": "NSArray",  # object holding array
    # macOS
    "window": "NSWindow",
    "application": "NSApplication",
    "menuItem": "NSMenuItem",
    "menu": "NSMenu",
    "control": "NSControl",
    "customView": "NSView",  # customView tag → NSView (Cocoa)
    "box": "NSBox",
    "splitView": "NSSplitView",
    "progressIndicator": "NSProgressIndicator",
    "stepper": "NSStepper",
    "slider": "NSSlider",
    "searchField": "NSSearchField",
    "secureTextField": "NSSecureTextField",
    "comboBox": "NSComboBox",
    "colorWell": "NSColorWell",
    "imageWell": "NSImageView",
    "matrix": "NSMatrix",
    "levelIndicator": "NSLevelIndicator",
    "datePicker": "NSDatePicker",
    "pathControl": "NSPathControl",
    "ruleView": "NSRuleView",
    "tokenField": "NSTokenField",
    "viewController": "NSViewController",
    "windowController": "NSWindowController",
    "tabViewController": "NSTabViewController",
    "pageController": "NSPageController",
    "splitViewController": "NSSplitViewController",
    # Outlet connection
    "outlet": "UIRuntimeOutletConnection",
    "action": "UIRuntimeOutletConnection",
}


def xib_tag_to_class(tag: str, custom_class: str = None) -> str:
    """xib の tag → NIB class 名の変換"""
    if custom_class:
        return custom_class
    return XIB_TAG_TO_CLASS.get(tag, tag)


# class 名 → xib tag への逆変換 (nib2xib で使用)
CLASS_TO_XIB_TAG = {v: k for k, v in XIB_TAG_TO_CLASS.items()}


# value type 推定
def guess_value_type(v):
    if v is None:
        return T_NIL
    if isinstance(v, bool):
        return T_TRUE if v else T_FALSE
    if isinstance(v, int):
        if -128 <= v <= 127:
            return T_INT8
        if -32768 <= v <= 32767:
            return T_INT16
        if -2**31 <= v <= 2**31 - 1:
            return T_INT32
        return T_INT64
    if isinstance(v, float):
        return T_DOUBLE
    if isinstance(v, bytes):
        return T_DATA
    if isinstance(v, str):
        return T_DATA  # string は data として
    return T_DATA


def build_nib_from_xib(doc: XIBDocument, strip: bool = False,
                          flatten: Optional[str] = None) -> NIBArchive:
    """xib ドキュメントを NIBArchive データ構造に変換

    strip: True ならデザイン時要素を除去
    flatten: 'YES' / 'NO' / None
        YES: Foundation Collection をインライン化 (ランタイム高速化)
        NO: ランタイムで展開
        None: デフォルト (通常 YES、build_nib_from_xib は常にインライン化するので影響なし)
    """
    arch = NIBArchive(format_version=1, coder_version=0x0a)

    # 1. Class names (NIB に必要な全 class を登録)
    classes: List[ClassName] = []
    class_index: dict = {}

    def add_class(cname: str) -> int:
        if cname not in class_index:
            class_index[cname] = len(classes)
            classes.append(ClassName(name=cname, extras=[]))
        return class_index[cname]

    # 必要 class を先に登録 (Apple nib の順に近い: NSObject, NSArray, UIProxyObject, ...)
    required_classes = [
        "NSObject", "NSArray", "UIProxyObject", "NSString",
        "UIRuntimeOutletConnection", "UIRuntimeActionConnection",
    ]
    for c in required_classes:
        add_class(c)

    # 実際の class を xib tag から決定
    obj_classes: List[str] = []
    for o in doc.objects:
        custom = o.attributes.get("customClass")
        cname = xib_tag_to_class(o.tag, custom)
        obj_classes.append(cname)
        add_class(cname)

    # xib の children で出てくる class も追加
    for o in doc.objects:
        for c in o.children:
            if c.tag in ("rect", "size", "point", "color", "font", "image", "string",
                         "window", "menu", "menuItem", "control"):
                cc = xib_tag_to_class(c.tag)
                add_class(cc)

    # Cocoa / CocoaTouch 共通の Foundation class
    for c in ("NSValue", "NSColor", "NSFont", "NSImage", "NSColorSpace", "NSFontDescriptor",
              "NSDictionary", "NSMutableArray", "NSMutableSet", "NSArray", "NSSet",
              "NSData", "NSNumber", "NSDate", "NSCalendar", "NSURL", "NSMutableString",
              "NSNib", "NSIBObjectData", "NSClassSwapper", "IBClassReference",
              "NSNibOutletConnector", "NSNibControlConnector"):
        add_class(c)

    # xib の connections から UIRuntimeOutletConnection / UIRuntimeActionConnection を登録
    for c in doc.connections:
        if c.type == "outlet":
            add_class("UIRuntimeOutletConnection")
        elif c.type == "action":
            add_class("UIRuntimeActionConnection")
    # xib 内の <connections>/<outlet> も同じく
    for o in doc.objects:
        for c in o.children:
            if c.tag == "connections":
                for cc in c.children:
                    if cc.tag == "outlet":
                        add_class("UIRuntimeOutletConnection")
                    elif cc.tag == "action":
                        add_class("UIRuntimeActionConnection")

    arch.class_names = classes

    # 2. Keys
    keys: List[Key] = []
    key_index: dict = {}

    def add_key(k: str) -> int:
        if k not in key_index:
            key_index[k] = len(keys)
            keys.append(Key(name=k))
        return key_index[k]

    # 必須キー (Apple nib の順に近い: $class, NSInlinedValue, UINibEncoderEmptyKey,
    # UINibTopLevelObjectsKey, UINibObjectsKey, UINibConnectionsKey, ...)
    required_keys = [
        "$class", "NSInlinedValue", "UINibEncoderEmptyKey",
        "UINibTopLevelObjectsKey", "UINibObjectsKey", "UINibConnectionsKey",
        "UINibVisibleWindowsKey", "UINibAccessibilityConfigurationsKey",
        "UINibKeyValuePairsKey", "UINibTraitStorageListsKey",
        "UIProxiedObjectIdentifier", "NS.bytes",
        "UIBounds", "UICenter", "UIBackgroundColor", "UIOpaque",
        "UIAutoresizeSubviews", "UIAutoresizingMask",
        "UIClearsContextBeforeDrawing", "UIViewSemanticContentAttribute",
        "UIDeepDrawRect", "UIViewLargeContentStoredProperties",
        "UISystemColorName", "UIColorComponentCount", "UIWhite", "UIAlpha",
        "NSWhite", "NSColorSpace",
        "UILayoutGuideIdentifier", "UILayoutGuideAllowsNegativeDimensions",
        "UILayoutGuideOwningViewIsLocked", "UILayoutGuideShouldBeArchived",
        "UIDestination", "UISource", "UILabel",
    ]
    for k in required_keys:
        add_key(k)

    # 実際のキー (xib の attributes から)
    for o in doc.objects:
        for k in o.attributes:
            add_key(k)
        for c in o.children:
            for k in c.attributes:
                add_key(k)
            for cc in c.children:
                for k in cc.attributes:
                    add_key(k)
    # 必須キーでカバーできない追加
    for c in doc.connections:
        add_key("UIDestination")
        add_key("UISource")
        add_key("UILabel")

    arch.keys = keys

    # 3. Coder values
    values: List[CoderValue] = []
    obj_to_value_start: List[int] = []
    obj_to_value_count: List[int] = []

    # 補助: str → nib value type への変換
    def make_value_for_attr(k: str, v, allow_objref: bool = True, objref_idx: int = -1):
        if isinstance(v, str) and v in ("YES", "NO"):
            return CoderValue(
                key_index=key_index[k], type=T_TRUE if v == "YES" else T_FALSE, data=None
            )
        if isinstance(v, str) and v == "":
            return CoderValue(key_index=key_index[k], type=T_NIL, data=None)
        if isinstance(v, str):
            # objref?
            if allow_objref and v.startswith("objref:"):
                idx = int(v.split(":", 1)[1])
                return CoderValue(key_index=key_index[k], type=T_OBJREF, data=None,
                                   is_objref=True, objref_index=idx)
            # 数値 (ASCII 文字のみで構成される場合のみ)
            if v and all(c in "0123456789.+-eE" for c in v):
                try:
                    if "." in v or "e" in v.lower():
                        return CoderValue(key_index=key_index[k], type=T_DOUBLE, data=float(v))
                    n = int(v)
                    t = guess_value_type(n)
                    return CoderValue(key_index=key_index[k], type=t, data=n)
                except (ValueError, TypeError):
                    pass
            # 文字列 (コントロール文字含む場合は DATA として)
            try:
                encoded = v.encode("utf-8")
            except UnicodeEncodeError:
                encoded = v.encode("utf-8", errors="replace")
            return CoderValue(key_index=key_index[k], type=T_DATA, data=encoded)
        if isinstance(v, bool):
            return CoderValue(
                key_index=key_index[k], type=T_TRUE if v else T_FALSE, data=None
            )
        if isinstance(v, int):
            t = guess_value_type(v)
            return CoderValue(key_index=key_index[k], type=t, data=v)
        if isinstance(v, float):
            return CoderValue(key_index=key_index[k], type=T_DOUBLE, data=v)
        if isinstance(v, bytes):
            return CoderValue(key_index=key_index[k], type=T_DATA, data=v)
        if v is None:
            return CoderValue(key_index=key_index[k], type=T_NIL, data=None)
        return CoderValue(key_index=key_index[k], type=T_DATA, data=str(v).encode("utf-8"))

    def append_value(k: str, v):
        ki = key_index.get(k)
        if ki is None:
            return
        values.append(make_value_for_attr(k, v))

    # 4. 各 object の value を作る
    obj_oid_index = {}  # xib id → NIB object index

    # 0a. placeholder が objref で参照する独立した <string> object の id を検出
    # xib id "obj-3" → placeholder の xib index (xib 内の index)
    placeholder_string_ref: Dict[int, str] = {}  # xib obj index → objref target id
    for oi, o in enumerate(doc.objects):
        # UIProxiedObjectIdentifier="obj-N" 属性
        ref = o.attributes.get("UIProxiedObjectIdentifier", "")
        if ref.startswith("obj-"):
            try:
                target_oi = int(ref.split("-", 1)[1])
                if 0 <= target_oi < len(doc.objects):
                    target_o = doc.objects[target_oi]
                    if target_o.tag == "string":
                        placeholder_string_ref[oi] = ref
            except ValueError:
                pass

    for oi, (o, cname) in enumerate(zip(doc.objects, obj_classes)):
        start = len(values)
        count = 0

        # $class
        values.append(CoderValue(
            key_index=key_index["$class"],
            type=T_OBJREF,
            data=None,
            is_objref=True,
            objref_index=class_index[cname],
        ))
        count += 1

        if cname == "UIProxyObject":
            # placeholder: NSInlinedValue=true + UINibEncoderEmptyKey
            values.append(CoderValue(
                key_index=key_index["NSInlinedValue"],
                type=T_TRUE, data=None
            ))
            count += 1
            # UIProxiedObjectIdentifier (object ref to NSString)
            # placeholder_string_ref に登録されている (objref 先) なら
            # 後で更新する (-1 を仮にセット)
            pl_id = o.attributes.get("placeholderIdentifier", "")
            if pl_id:
                values.append(CoderValue(
                    key_index=key_index["UIProxiedObjectIdentifier"],
                    type=T_OBJREF,
                    data=None,
                    is_objref=True,
                    objref_index=-1,  # placeholder 後に更新
                ))
                count += 1

        # 属性 → value
        for k, v in o.attributes.items():
            if k in ("id", "placeholderIdentifier", "customClass", "UIProxiedObjectIdentifier"):
                continue
            # outlet/action の独立 object の場合の特別処理
            if cname in ("UIRuntimeOutletConnection", "UIRuntimeActionConnection"):
                if k == "UISource" and v.startswith("obj-"):
                    # objref として書く
                    try:
                        src_idx = int(v.split("-", 1)[1])
                        if 0 <= src_idx < len(obj_to_value_start):
                            values.append(CoderValue(
                                key_index=key_index["UISource"],
                                type=T_OBJREF,
                                data=None,
                                is_objref=True,
                                objref_index=src_idx,
                            ))
                            count += 1
                            continue
                    except ValueError:
                        pass
                elif k == "UIDestination" and v.startswith("obj-"):
                    try:
                        dst_idx = int(v.split("-", 1)[1])
                        if 0 <= dst_idx < len(obj_to_value_start):
                            values.append(CoderValue(
                                key_index=key_index["UIDestination"],
                                type=T_OBJREF,
                                data=None,
                                is_objref=True,
                                objref_index=dst_idx,
                            ))
                            count += 1
                            continue
                    except ValueError:
                        pass
                elif k == "UILabel" and v.startswith("obj-"):
                    # UILabel が objref の場合 (NSString を指す)
                    try:
                        ref_idx = int(v.split("-", 1)[1])
                        if 0 <= ref_idx < len(obj_to_value_start):
                            values.append(CoderValue(
                                key_index=key_index["UILabel"],
                                type=T_OBJREF,
                                data=None,
                                is_objref=True,
                                objref_index=ref_idx,
                            ))
                            count += 1
                            continue
                    except ValueError:
                        pass
            append_value(k, v)
            count += 1

        # 子要素 (rect, color, font, image, string, ...)
        for c in o.children:
            cc_cname = xib_tag_to_class(c.tag)
            if c.tag in ("connections",):
                # connections は connection object として別途作成
                continue
            if c.tag in ("outlet", "action"):
                # 個別の UIRuntimeOutletConnection として別途作成
                continue
            if c.tag in ("string", "font", "color", "image"):
                # 子要素の value を作る (1 value: $class + 1 attr)
                # この object の value として取り込み
                # 簡易: 1 attribute のみ
                for k, v in c.attributes.items():
                    if k == "id":
                        continue
                    append_value(k, v)
                    count += 1
            else:
                # rect / size / point などの子要素
                for k, v in c.attributes.items():
                    if k == "id" or k == "key":
                        continue
                    append_value(k, v)
                    count += 1

        obj_to_value_start.append(start)
        obj_to_value_count.append(count)

    # 5. 個別の UIRuntimeOutletConnection / UIRuntimeActionConnection を作る
    # 5a. xib の <connections> トップレベル
    for conn in doc.connections:
        # UIRuntimeOutletConnection
        start = len(values)
        count = 0
        # $class
        cls_name = "UIRuntimeOutletConnection" if conn.type == "outlet" else "UIRuntimeActionConnection"
        values.append(CoderValue(
            key_index=key_index["$class"],
            type=T_OBJREF,
            data=None,
            is_objref=True,
            objref_index=class_index[cls_name],
        ))
        count += 1
        # UISource
        # 解決: conn.source_id → NIB object index
        src_idx = -1
        for i, o in enumerate(doc.objects):
            if o.id == conn.source_id:
                src_idx = i
                break
        if src_idx >= 0:
            values.append(CoderValue(
                key_index=key_index["UISource"],
                type=T_OBJREF,
                data=None,
                is_objref=True,
                objref_index=src_idx,
            ))
            count += 1
        # UIDestination
        dst_idx = -1
        for i, o in enumerate(doc.objects):
            if o.id == conn.destination_id:
                dst_idx = i
                break
        if dst_idx >= 0:
            values.append(CoderValue(
                key_index=key_index["UIDestination"],
                type=T_OBJREF,
                data=None,
                is_objref=True,
                objref_index=dst_idx,
            ))
            count += 1
        # UILabel (connection 名)
        if conn.label:
            values.append(CoderValue(
                key_index=key_index["UILabel"],
                type=T_DATA,
                data=conn.label.encode("utf-8"),
            ))
            count += 1
        # この connection を object として追加
        obj_to_value_start.append(start)
        obj_to_value_count.append(count)

    # 5b. xib の <placeholder>/<connections>/<outlet>
    for oi, o in enumerate(doc.objects):
        for c in o.children:
            if c.tag != "connections":
                continue
            for cc in c.children:
                if cc.tag not in ("outlet", "action"):
                    continue
                # 独立した <outlet> / <action> object として既に存在する場合は
                # 新規作成しない (nib2xib の出力で outlet が独立 object として
                # 作られる場合に重複しないように)
                outlet_id = cc.attributes.get("id", "")
                if outlet_id and any(oo.id == outlet_id for oo in doc.objects):
                    continue
                start = len(values)
                count = 0
                cls_name = "UIRuntimeOutletConnection" if cc.tag == "outlet" else "UIRuntimeActionConnection"
                values.append(CoderValue(
                    key_index=key_index["$class"],
                    type=T_OBJREF,
                    data=None,
                    is_objref=True,
                    objref_index=class_index[cls_name],
                ))
                count += 1
                # UISource = oi
                values.append(CoderValue(
                    key_index=key_index["UISource"],
                    type=T_OBJREF,
                    data=None,
                    is_objref=True,
                    objref_index=oi,
                ))
                count += 1
                # UIDestination
                dst = cc.attributes.get("destination", "")
                dst_idx = -1
                for j, oo in enumerate(doc.objects):
                    if oo.id == dst:
                        dst_idx = j
                        break
                if dst_idx >= 0:
                    values.append(CoderValue(
                        key_index=key_index["UIDestination"],
                        type=T_OBJREF,
                        data=None,
                        is_objref=True,
                        objref_index=dst_idx,
                    ))
                    count += 1
                # label
                label = cc.attributes.get("property", "") or cc.attributes.get("selector", "")
                if label:
                    values.append(CoderValue(
                        key_index=key_index["UILabel"],
                        type=T_DATA,
                        data=label.encode("utf-8"),
                    ))
                    count += 1
                obj_to_value_start.append(start)
                obj_to_value_count.append(count)

    # 6. UIProxyObject の NSString オブジェクト
    # (placeholder → UIProxiedObjectIdentifier の先)
    proxy_string_indices = []  # 各 placeholder の NSString object index
    # 独立した <string> object を後で参照できるよう、xib id → NIB object index の map
    # placeholder_string_ref (placeholder obj index → objref target id) を使う
    string_id_to_nib_idx = {}  # "obj-3" → NIB object index
    # 既に NIB objects に含まれている独立 string を先に記録
    for oi2, o2 in enumerate(doc.objects):
        if o2.tag == "string":
            # この string は oi2 として既に NIB object に作られる
            string_id_to_nib_idx[o2.id] = oi2

    for oi, o in enumerate(doc.objects):
        if obj_classes[oi] != "UIProxyObject":
            continue
        pl_id = o.attributes.get("placeholderIdentifier", "")
        # 独立した <string> objref があるか確認
        if oi in placeholder_string_ref:
            target_id = placeholder_string_ref[oi]
            # 既に NIB に作られているはず
            target_idx = string_id_to_nib_idx.get(target_id, -1)
            if target_idx >= 0:
                # 新規 NSString を作らず、proxy_string_indices に target_idx を記録
                proxy_string_indices.append(target_idx)
                continue
        # 新規 NSString を作る
        start = len(values)
        count = 0
        values.append(CoderValue(
            key_index=key_index["$class"],
            type=T_OBJREF,
            data=None,
            is_objref=True,
            objref_index=class_index["NSString"],
        ))
        count += 1
        # NSInlinedValue
        values.append(CoderValue(
            key_index=key_index["NSInlinedValue"],
            type=T_TRUE, data=None
        ))
        count += 1
        # NS.bytes
        values.append(CoderValue(
            key_index=key_index["NS.bytes"],
            type=T_DATA,
            data=pl_id.encode("utf-8"),
        ))
        count += 1
        obj_to_value_start.append(start)
        obj_to_value_count.append(count)
        proxy_string_indices.append(len(obj_to_value_start) - 1)

    # 7. UIProxyObject の UIProxiedObjectIdentifier 値に NSString index を入れる
    # 走査して、objToValues の UIProxiedObjectIdentifier を正しい index に書き換え
    psi = 0
    for oi, cname in enumerate(obj_classes):
        if cname != "UIProxyObject":
            continue
        if psi >= len(proxy_string_indices):
            break
        # 該当 object の value を走査して UIProxiedObjectIdentifier の objref を更新
        start = obj_to_value_start[oi]
        count = obj_to_value_count[oi]
        for j in range(start, start + count):
            v = values[j]
            ki = arch.keys[v.key_index].name if v.key_index < len(arch.keys) else None
            if ki == "UIProxiedObjectIdentifier" and v.is_objref:
                v.objref_index = proxy_string_indices[psi]
        psi += 1

    # 8. BackgroundColor の UIColor オブジェクト
    # backgroundColor="objref:7" のような参照は、上記の build で対応。
    # ここでは color/font オブジェクトは作らず、placeholder の NSString のみ。
    # xib 内の <color>/<font> 子要素がある場合は別途作る必要がある。
    # → 簡易: backgroundColor 文字列が "systemBackgroundColor" の場合、
    #   UIColor object + UISystemColorName の NSString を作る
    # 簡易化: 各 object の children で color/font タグがあれば作る
    color_obj_indices = {}  # background_color objref name → index
    for oi, o in enumerate(doc.objects):
        for c in o.children:
            if c.tag not in ("color", "font", "image", "string"):
                continue
            # 子要素の id を取得
            sub_id = c.attributes.get("id", "")
            if not sub_id:
                continue
            cc_cname = xib_tag_to_class(c.tag)
            start = len(values)
            count = 0
            values.append(CoderValue(
                key_index=key_index["$class"],
                type=T_OBJREF,
                data=None,
                is_objref=True,
                objref_index=class_index[cc_cname],
            ))
            count += 1
            if c.tag == "color":
                # NSInlinedValue
                values.append(CoderValue(
                    key_index=key_index["NSInlinedValue"],
                    type=T_TRUE, data=None
                ))
                count += 1
                for k, v in c.attributes.items():
                    if k == "id":
                        continue
                    append_value(k, v)
                    count += 1
                # UISystemColorName がある場合、NSString を作る
                sys_name = c.attributes.get("systemColor", "")
                if sys_name:
                    # 内部 NSString を作る
                    sub_start = len(values)
                    sub_count = 0
                    values.append(CoderValue(
                        key_index=key_index["$class"],
                        type=T_OBJREF,
                        data=None,
                        is_objref=True,
                        objref_index=class_index["NSString"],
                    ))
                    sub_count += 1
                    values.append(CoderValue(
                        key_index=key_index["NSInlinedValue"],
                        type=T_TRUE, data=None
                    ))
                    sub_count += 1
                    values.append(CoderValue(
                        key_index=key_index["NS.bytes"],
                        type=T_DATA,
                        data=sys_name.encode("utf-8"),
                    ))
                    sub_count += 1
                    obj_to_value_start.append(sub_start)
                    obj_to_value_count.append(sub_count)
                    # UISystemColorName の値として NSString object への参照
                    append_value("UISystemColorName", "objref:%d" % (len(obj_to_value_start) - 1))
                    count += 1
            elif c.tag == "string":
                for k, v in c.attributes.items():
                    if k == "id":
                        continue
                    append_value(k, v)
                    count += 1
            else:
                for k, v in c.attributes.items():
                    if k == "id":
                        continue
                    append_value(k, v)
                    count += 1
            obj_to_value_start.append(start)
            obj_to_value_count.append(count)
            color_obj_indices[sub_id] = len(obj_to_value_start) - 1

    # 9. backgroundColor などの属性で "objref:N" 形式があれば更新
    for oi, o in enumerate(doc.objects):
        for k, v in o.attributes.items():
            if isinstance(v, str) and v.startswith("objref:"):
                ref_idx = int(v.split(":", 1)[1])
                if ref_idx < len(obj_to_value_start):
                    # 該当 key_index の value を探す
                    start = obj_to_value_start[oi]
                    count = obj_to_value_count[oi]
                    for j in range(start, start + count):
                        vv = values[j]
                        ki = arch.keys[vv.key_index].name if vv.key_index < len(arch.keys) else None
                        if ki == k and vv.is_objref:
                            vv.objref_index = ref_idx

    # 10. layoutGuide の NSString
    # 10a. layoutGuide が UILayoutGuideIdentifier で objref する独立した <string> を検出
    layoutguide_string_ref: Dict[int, int] = {}  # layoutguide oi → target oi
    for oi, o in enumerate(doc.objects):
        if obj_classes[oi] != "UILayoutGuide":
            continue
        ref = o.attributes.get("UILayoutGuideIdentifier", "")
        if ref.startswith("obj-"):
            try:
                target_oi = int(ref.split("-", 1)[1])
                if 0 <= target_oi < len(doc.objects):
                    if doc.objects[target_oi].tag == "string":
                        layoutguide_string_ref[oi] = target_oi
            except ValueError:
                pass

    for oi, o in enumerate(doc.objects):
        if obj_classes[oi] != "UILayoutGuide":
            continue
        # 独立した <string> objref がある場合
        if oi in layoutguide_string_ref:
            target_oi = layoutguide_string_ref[oi]
            # 既に NIB objects に含まれているはず
            # 4. のループで doc.objects[target_oi] は NIB object index = target_oi として作られている
            # (obj_classes と NIB objects の最初の N=len(obj_classes) 個は同期)
            if target_oi < len(obj_to_value_start):
                # UILayoutGuideIdentifier の objref を更新
                start = obj_to_value_start[oi]
                count = obj_to_value_count[oi]
                for j in range(start, start + count):
                    vv = values[j]
                    ki = arch.keys[vv.key_index].name if vv.key_index < len(arch.keys) else None
                    if ki == "UILayoutGuideIdentifier" and vv.is_objref:
                        vv.objref_index = target_oi
                continue
        # 子が <string> の場合の従来ロジック
        for c in o.children:
            if c.tag != "string":
                continue
            sub_id = c.attributes.get("id", "")
            if not sub_id:
                continue
            start = len(values)
            count = 0
            values.append(CoderValue(
                key_index=key_index["$class"],
                type=T_OBJREF,
                data=None,
                is_objref=True,
                objref_index=class_index["NSString"],
            ))
            count += 1
            values.append(CoderValue(
                key_index=key_index["NSInlinedValue"],
                type=T_TRUE, data=None
            ))
            count += 1
            for k, v in c.attributes.items():
                if k == "id":
                    continue
                append_value(k, v)
                count += 1
            obj_to_value_start.append(start)
            obj_to_value_count.append(count)
            layout_idx = len(obj_to_value_start) - 1
            start2 = obj_to_value_start[oi]
            count2 = obj_to_value_count[oi]
            for j in range(start2, start2 + count2):
                vv = values[j]
                ki = arch.keys[vv.key_index].name if vv.key_index < len(arch.keys) else None
                if ki == "UILayoutGuideIdentifier" and vv.is_objref:
                    vv.objref_index = layout_idx

    arch.values = values

    # 11. Objects
    objects: List[Object] = []
    for oi, cname in enumerate(obj_classes):
        objects.append(Object(
            class_index=class_index[cname],
            value_start=obj_to_value_start[oi] if oi < len(obj_to_value_start) else 0,
            value_count=obj_to_value_count[oi] if oi < len(obj_to_value_count) else 0,
        ))
    # 残りの objects (connections, NSString, UIRuntimeOutletConnection 等)
    for oi in range(len(obj_classes), len(obj_to_value_start)):
        # 既存の objects リストの後ろに追加
        # この object の class は values の先頭 ($class) から推定
        start = obj_to_value_start[oi]
        if start < len(values) and values[start].key_index < len(arch.keys):
            ki = arch.keys[values[start].key_index].name
            if ki == "$class" and values[start].is_objref:
                cname_idx = values[start].objref_index
                if cname_idx < len(arch.class_names):
                    cname = arch.class_names[cname_idx].name
                else:
                    cname = "NSObject"
            else:
                cname = "NSObject"
        else:
            cname = "NSObject"
        objects.append(Object(
            class_index=class_index.get(cname, class_index["NSObject"]),
            value_start=start,
            value_count=obj_to_value_count[oi],
        ))
    arch.objects = objects

    return arch


def _walk(o: XIBObject):
    yield o
    for c in o.children:
        yield c
        yield from _walk_children(c)


def _walk_children(e: XIBElement):
    yield e
    for c in e.children:
        yield from _walk_children(c)


def compile_to_nib(doc: XIBDocument, args, strip: bool = False) -> bytes:
    """xib → NIBArchive バイナリ"""
    from .nibarchive import build_nib
    flatten = None
    if args is not None:
        flatten = getattr(args, 'flatten', None)
    arch = build_nib_from_xib(doc, strip=strip, flatten=flatten)
    return build_nib(arch)
