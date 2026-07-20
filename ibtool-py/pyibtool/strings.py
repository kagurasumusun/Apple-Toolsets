"""
ibtool の strings / xliff ローカライズファイル生成・適用

.apple/Base.lproj/Localizable.strings の標準形式。
"""

from typing import List
from .xibdoc import XIBDocument, XIBObject, XIBElement


# xib 内の localizable な属性名の集合
LOCALIZABLE_KEYS = [
    "title", "text", "placeholder", "prompt", "label",
    "accessibilityLabel", "accessibilityHint",
    "headerTitle", "footerTitle",
]


def generate_strings(doc: XIBDocument, empty_values: bool = False) -> str:
    """xib から .strings ファイル形式を生成。
    empty_values=True なら --generate-strings-file 用 (空文字で出力)
    """
    lines = []
    seen = set()
    for o in doc.objects:
        for e in _walk(o):
            for k in LOCALIZABLE_KEYS:
                if k in e.attributes:
                    v = e.attributes[k]
                    if v and v.strip() or empty_values:
                        key = _escape_key("\"%s.%s\"" % (o.id, k))
                        if key in seen:
                            continue
                        seen.add(key)
                        if empty_values:
                            val = "\"\";"
                        else:
                            val = _escape_value(v)
                        lines.append("%s = %s" % (key, val))
    if not lines:
        # Apple ibtool の挙動: 空でも何か返す
        return ""
    return "\n".join(lines) + "\n"


def _walk(o: XIBObject):
    yield o
    for c in o.children:
        yield c
        yield from _walk_children(c)


def _walk_children(e: XIBElement):
    yield e
    for c in e.children:
        yield from _walk_children(c)


def _escape_key(s: str) -> str:
    # Apple の strings ファイル形式では key を "..." で囲む
    return s  # 既に "..." 形式


def _escape_value(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace("\"", "\\\"")
    s = s.replace("\n", "\\n")
    s = s.replace("\t", "\\t")
    return "\"%s\";" % s


def apply_strings(doc: XIBDocument, strings_text: str) -> None:
    """strings ファイルを xib に適用"""
    entries = _parse_strings(strings_text)
    for o in doc.objects:
        for e in _walk(o):
            for k in LOCALIZABLE_KEYS:
                key = "\"%s.%s\"" % (o.id, k)
                if key in entries:
                    e.attributes[k] = entries[key]


def _parse_strings(text: str) -> dict:
    """Apple 形式 strings ファイル -> dict"""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("/*"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().rstrip(";")
        # 簡易展開: 囲みの " を除き、エスケープを展開
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        v = v.replace("\\n", "\n").replace("\\t", "\t")
        v = v.replace("\\\"", "\"").replace("\\\\", "\\")
        out[k] = v
    return out
