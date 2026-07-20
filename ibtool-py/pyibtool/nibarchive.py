"""
NIBArchive 完全実装 (Mac 非依存 / pure Python)

フォーマット仕様 (mothersruin.com/Archaeology 解析結果 + 実機フィクスチャ観察):

Header (50 bytes):
  0..9    magic "NIBArchive"
  10..13  formatVersion (u32 LE)  = 1
  14..17  coderVersion (u32 LE)   = 0x0a (10) on macOS 10.15+; 0x09 in older
  18..21  objectCount (u32 LE)
  22..25  objectOffset (u32 LE)
  26..29  keyStringCount (u32 LE)
  30..33  keyStringOffset (u32 LE)
  34..37  coderValueCount (u32 LE)
  38..41  coderValueOffset (u32 LE)
  42..45  classNameCount (u32 LE)
  46..49  classNameOffset (u32 LE)

Tables (順番に object → key → value → class):
  Object: (varint class_idx, varint value_start, varint value_count)
  Key:    (varint length, UTF-8 string, no NUL)
  Value:  (varint key_idx, u8 type, data per type)
    type:
      0 = int8    (1 byte)
      1 = int16   (2 bytes LE)
      2 = int32   (4 bytes LE)
      3 = int64   (8 bytes LE)
      4 = true
      5 = false
      6 = float   (4 bytes LE)
      7 = double  (8 bytes LE)
      8 = data    (varint length, N bytes)
      9 = nil
      10 = object reference (u32 LE - offset into objects table)
  Class:  (varint length, varint extras_count, [int32 LE] * extras_count, UTF-8 string)

Varint: 7-bit LE, high bit = continuation.
"""

import struct
import io
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union


# value type コード
T_INT8    = 0
T_INT16   = 1
T_INT32   = 2
T_INT64   = 3
T_TRUE    = 4
T_FALSE   = 5
T_FLOAT   = 6
T_DOUBLE  = 7
T_DATA    = 8
T_NIL     = 9
T_OBJREF  = 10


# 値のデータ
@dataclass
class CoderValue:
    key_index: int
    type: int
    data: Union[int, float, bytes, None, Tuple[int, int]]  # objref は (index) のタプル
    # objref の場合は data = {"ref": int} とする
    is_objref: bool = False
    objref_index: int = 0

    def __repr__(self):
        if self.type == T_NIL:
            return f"CV(nil)"
        if self.type == T_TRUE:
            return f"CV(true)"
        if self.type == T_FALSE:
            return f"CV(false)"
        if self.type == T_OBJREF:
            return f"CV(objref@{self.objref_index})"
        return f"CV(type={self.type}, data={self.data!r})"


@dataclass
class Key:
    name: str


@dataclass
class Object:
    class_index: int
    value_start: int  # coder value index
    value_count: int


@dataclass
class ClassName:
    name: str
    extras: List[int] = field(default_factory=list)


@dataclass
class NIBArchive:
    format_version: int = 1
    coder_version: int = 0x0a
    object_count: int = 0
    object_offset: int = 0
    key_count: int = 0
    key_offset: int = 0
    value_count: int = 0
    value_offset: int = 0
    class_count: int = 0
    class_offset: int = 0
    has_lne_trailer: bool = True  # Xcode 13+ の nib は末尾に "LNE\0" 4 byte trailer
    # フルデコードされたテーブル (Xcode 26.5 の nib では部分的/失敗)
    objects: List[Object] = field(default_factory=list)
    keys: List[Key] = field(default_factory=list)
    values: List[CoderValue] = field(default_factory=list)
    class_names: List[ClassName] = field(default_factory=list)
    # 生バイト (デコード失敗時のフォールバック)
    raw_body: bytes = b""

    def lookup_key(self, idx):
        if 0 <= idx < len(self.keys):
            return self.keys[idx].name
        return None

    def lookup_class(self, idx):
        if 0 <= idx < len(self.class_names):
            return self.class_names[idx].name
        return None


def read_vint(data: bytes, pos: int) -> Tuple[int, int]:
    """VInt を読み、(value, new_pos) を返す

    nibsqueeze / Archaeology 仕様 + nibarchive パッケージ実装に準拠:
      - high bit 1 = last byte (terminator)
      - high bit 0 = continuation
      - 7 bits per byte, little-endian order
    """
    val = 0
    shift = 0
    # 安全弁: 最大 5 byte
    for _ in range(5):
        if pos >= len(data):
            raise IndexError("read_vint: out of data at %d (len=%d)" % (pos, len(data)))
        b = data[pos]
        pos += 1
        val |= (b & 0x7f) << shift
        if b & 0x80:
            # high bit 1 = last byte (terminator)
            return val, pos
        # high bit 0 = continuation
        shift += 7
    return val, pos


def write_vint(val: int) -> bytes:
    """VInt を書く (high bit 1 = terminator, 0 = continuation)"""
    if val < 0:
        raise ValueError("VInt must be non-negative: %d" % val)
    if val == 0:
        return b"\x80"  # 0 → 0x80 (1 byte, high bit 1 = terminator)
    out = bytearray()
    # 値を 7-bit チャンクに分割
    while val:
        b = val & 0x7f
        val >>= 7
        if val == 0:
            # last byte
            out.append(b | 0x80)
        else:
            out.append(b)
    return bytes(out)


def read_u8(data, pos):
    return data[pos], pos + 1


def read_u16(data, pos):
    return struct.unpack_from("<H", data, pos)[0], pos + 2


def read_u32(data, pos):
    return struct.unpack_from("<I", data, pos)[0], pos + 4


def read_i8(data, pos):
    return struct.unpack_from("<b", data, pos)[0], pos + 1


def read_i16(data, pos):
    return struct.unpack_from("<h", data, pos)[0], pos + 2


def read_i32(data, pos):
    return struct.unpack_from("<i", data, pos)[0], pos + 4


def read_i64(data, pos):
    return struct.unpack_from("<q", data, pos)[0], pos + 8


def read_f32(data, pos):
    return struct.unpack_from("<f", data, pos)[0], pos + 4


def read_f64(data, pos):
    return struct.unpack_from("<d", data, pos)[0], pos + 8


def parse_nib(data: bytes) -> NIBArchive:
    if data[:10] != b"NIBArchive":
        raise ValueError("not a NIBArchive (magic mismatch): %r" % data[:10])
    # Archaeology 記事に従い +0a から u32 を 10 個読む
    fv = struct.unpack_from("<I", data, 0x0a)[0]
    cv = struct.unpack_from("<I", data, 0x0e)[0]
    obj_count = struct.unpack_from("<I", data, 0x12)[0]
    obj_off = struct.unpack_from("<I", data, 0x16)[0]
    key_count = struct.unpack_from("<I", data, 0x1a)[0]
    key_off = struct.unpack_from("<I", data, 0x1e)[0]
    val_count = struct.unpack_from("<I", data, 0x22)[0]
    val_off = struct.unpack_from("<I", data, 0x26)[0]
    cls_count = struct.unpack_from("<I", data, 0x2a)[0]
    cls_off = struct.unpack_from("<I", data, 0x2e)[0]

    # LNE\0 trailer の検出: 末尾 4 byte が "LNE\0" なら新形式
    has_lne_trailer = False
    if len(data) >= 4 and data[-4:] == b"LNE\x00":
        has_lne_trailer = True

    arch = NIBArchive(format_version=fv, coder_version=cv,
                      object_count=obj_count, object_offset=obj_off,
                      key_count=key_count, key_offset=key_off,
                      value_count=val_count, value_offset=val_off,
                      class_count=cls_count, class_offset=cls_off,
                      has_lne_trailer=has_lne_trailer,
                      raw_body=data[0x32:])

    # テーブル読み込みを試みる (Xcode 26.5 の nib で失敗する可能性あり)
    # 失敗したらスキップして生 body だけ保持
    try:
        # Objects
        pos = obj_off
        for _ in range(obj_count):
            class_idx, pos = read_vint(data, pos)
            value_start, pos = read_vint(data, pos)
            value_count, pos = read_vint(data, pos)
            arch.objects.append(Object(class_index=class_idx,
                                       value_start=value_start,
                                       value_count=value_count))

        # Keys
        pos = key_off
        for _ in range(key_count):
            n, pos = read_vint(data, pos)
            s = data[pos:pos + n].decode("utf-8", errors="replace")
            pos += n
            arch.keys.append(Key(name=s))

        # Values
        pos = val_off
        for _ in range(val_count):
            key_idx, pos = read_vint(data, pos)
            t, pos = read_u8(data, pos)
            if t == T_NIL:
                v = CoderValue(key_index=key_idx, type=t, data=None)
            elif t == T_TRUE:
                v = CoderValue(key_index=key_idx, type=t, data=True)
            elif t == T_FALSE:
                v = CoderValue(key_index=key_idx, type=t, data=False)
            elif t == T_INT8:
                x, pos = read_i8(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=x)
            elif t == T_INT16:
                x, pos = read_i16(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=x)
            elif t == T_INT32:
                x, pos = read_i32(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=x)
            elif t == T_INT64:
                x, pos = read_i64(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=x)
            elif t == T_FLOAT:
                x, pos = read_f32(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=x)
            elif t == T_DOUBLE:
                x, pos = read_f64(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=x)
            elif t == T_DATA:
                n, pos = read_vint(data, pos)
                b = data[pos:pos + n]
                pos += n
                v = CoderValue(key_index=key_idx, type=t, data=b)
            elif t == T_OBJREF:
                x, pos = read_u32(data, pos)
                v = CoderValue(key_index=key_idx, type=t, data=None,
                               is_objref=True, objref_index=x)
            else:
                raise ValueError("unknown value type %d" % t)
            arch.values.append(v)

        # Class names
        pos = cls_off
        for _ in range(cls_count):
            n, pos = read_vint(data, pos)
            extras_count, pos = read_vint(data, pos)
            extras = []
            for _ in range(extras_count):
                x, pos = read_i32(data, pos)
                extras.append(x)
            s = data[pos:pos + n].decode("utf-8", errors="replace")
            # NUL 終端を除去
            if s.endswith("\x00"):
                s = s[:-1]
            pos += n
            arch.class_names.append(ClassName(name=s, extras=extras))
    except (IndexError, ValueError) as e:
        # Xcode 26.5 の nib など、テーブル形式が未知の場合は部分読み込み
        # raw_body にフォールバック
        sys.stderr.write("nibarchive.parse_nib: partial decode (%s)\n" % e)
        # 既に読んだ分はそのまま残す
    return arch


def build_nib(arch: NIBArchive) -> bytes:
    """NIBArchive バイナリを生成"""
    out = io.BytesIO()
    # header
    out.write(b"NIBArchive")
    out.write(struct.pack("<I", arch.format_version))
    out.write(struct.pack("<I", arch.coder_version))
    # placeholders for counts/offsets (8 fields)
    for _ in range(8):
        out.write(b"\x00\x00\x00\x00")

    # objects
    obj_off = out.tell()
    for o in arch.objects:
        out.write(write_vint(o.class_index))
        out.write(write_vint(o.value_start))
        out.write(write_vint(o.value_count))
    # 4 byte padding を追加 (元の nib は 16 obj × 3 byte = 48, no padding)
    # ただし次の key table を 4 byte アラインするために padding が必要な場合あり
    # ここでは padding を追加しない (元の nib と同じ)

    # keys
    key_off = out.tell()
    for k in arch.keys:
        b = k.name.encode("utf-8")
        out.write(write_vint(len(b)))
        out.write(b)
    # Apple nib と同じ: padding なし (次のテーブルは直後に始まる)

    # values
    val_off = out.tell()
    for v in arch.values:
        out.write(write_vint(v.key_index))
        out.write(struct.pack("B", v.type))
        if v.type == T_NIL:
            pass
        elif v.type in (T_TRUE, T_FALSE):
            pass
        elif v.type == T_INT8:
            out.write(struct.pack("<b", v.data))
        elif v.type == T_INT16:
            out.write(struct.pack("<h", v.data))
        elif v.type == T_INT32:
            out.write(struct.pack("<i", v.data))
        elif v.type == T_INT64:
            out.write(struct.pack("<q", v.data))
        elif v.type == T_FLOAT:
            out.write(struct.pack("<f", v.data))
        elif v.type == T_DOUBLE:
            out.write(struct.pack("<d", v.data))
        elif v.type == T_DATA:
            out.write(write_vint(len(v.data)))
            out.write(v.data)
        elif v.type == T_OBJREF:
            out.write(struct.pack("<I", v.objref_index))
        else:
            raise ValueError("unsupported type %d" % v.type)
    # value table 終端に padding なし (class table offset まで直接)

    # class names
    cls_off = out.tell()
    for c in arch.class_names:
        b = c.name.encode("utf-8") + b"\x00"  # NUL 終端
        out.write(write_vint(len(b)))
        out.write(write_vint(len(c.extras)))
        for x in c.extras:
            out.write(struct.pack("<i", x))
        out.write(b)
    # 4 byte trailer "LNE\0" (Xcode 13+ の nib に存在、古い nib には無い)
    if arch.has_lne_trailer:
        out.write(b"LNE\x00")

    # header を更新
    data = out.getvalue()
    data = bytearray(data)
    struct.pack_into("<I", data, 0x12, len(arch.objects))
    struct.pack_into("<I", data, 0x16, obj_off)
    struct.pack_into("<I", data, 0x1a, len(arch.keys))
    struct.pack_into("<I", data, 0x1e, key_off)
    struct.pack_into("<I", data, 0x22, len(arch.values))
    struct.pack_into("<I", data, 0x26, val_off)
    struct.pack_into("<I", data, 0x2a, len(arch.class_names))
    struct.pack_into("<I", data, 0x2e, cls_off)
    return bytes(data)


# 簡易ダンプ
def dump(arch: NIBArchive, depth=0):
    ind = "  " * depth
    print(f"{ind}=== NIBArchive ===")
    print(f"{ind}formatVersion={arch.format_version} coderVersion=0x{arch.coder_version:x}")
    print(f"{ind}objects={len(arch.objects)} keys={len(arch.keys)} values={len(arch.values)} classNames={len(arch.class_names)}")
    print(f"{ind}--- Keys ---")
    for i, k in enumerate(arch.keys):
        print(f"{ind}  [{i:3d}] {k.name!r}")
    print(f"{ind}--- Class names ---")
    for i, c in enumerate(arch.class_names):
        print(f"{ind}  [{i:3d}] {c.name!r} extras={c.extras}")
    print(f"{ind}--- Objects ---")
    for i, o in enumerate(arch.objects):
        cname = arch.lookup_class(o.class_index)
        print(f"{ind}  [{i:3d}] class={cname!r} values=[{o.value_start}..{o.value_start + o.value_count})")
        for j in range(o.value_start, o.value_start + o.value_count):
            if j < len(arch.values):
                v = arch.values[j]
                k = arch.lookup_key(v.key_index)
                print(f"{ind}        {k!r} = {v!r}")


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        with open(path, "rb") as f:
            data = f.read()
        arch = parse_nib(data)
        dump(arch)
        print()
