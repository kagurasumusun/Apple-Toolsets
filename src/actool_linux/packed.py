"""CoreUI packed-asset (ZZZZPackedAsset / LINK) writer.

Observed Apple behavior (Xcode 26.x oracles; derived only from observable
outputs on independently created inputs):

When a catalog emits an APPEARANCEKEYS or LOCALIZATIONKEYS registry, Apple
replaces the pixel data of every scale-1, non-localized, universal-idiom
RGB(A) image rendition with a "packed asset" reference:

- The rendition becomes layout 1003 with TLVs [1001, 1003, 1010, 1004, 1006]
  and an empty payload. TLV 1010 ("LINK") carries the (x, y, w, h) rectangle
  inside the atlas plus the key of the atlas rendition.
- One layout-1004 atlas rendition is emitted per appearance value that has
  at least two candidates. Its CoreUI key is identifier=0, element=9,
  part=181, scale=1, appearance=A. It has NO facet entry and NO bitmap value.
- Atlas payload: MLEC mode 2 codec 11 wrapping dmp2: palette grammar v4
  (<=256 distinct colors, swatch 0 = transparent padding) or raw-BGRA LZFSE
  grammar v2. Pixels are premultiplied BGRA; atlas padding is transparent.
- Grayscale (" 8AG", bpp 2) images, localized renditions, non-1x scales and
  idiom-specific renditions are never packed.

The exact Apple bin-packing heuristic is private; this module uses a
deterministic shelf packer. Offsets written into LINK renditions always
match our own atlas, so consumer resolution is unaffected (documented
cosmetic difference).
"""
from __future__ import annotations

import struct
from dataclasses import replace

from .carwriter import AssetRendition, _fixed, lzfse_compat

PACKED_ASSET_NAME = "ZZZZPackedAsset-1.1.0-gamut0"
ATLAS_PADDING = 2
_LINK_MAGIC = bytes.fromhex("4b4c4e49")


def _decode_deepmap_bgra(csi: bytes) -> tuple[int, int, bytes] | None:
    """Recover premultiplied BGRA pixels from a layout-12 deepmap CSI.

    Understands the grammars this package emits: v1 raw, v2 LZFSE BGRA and
    v4 palette+index (bpp 4). Returns None for anything else so callers can
    leave the rendition untouched.
    """
    if len(csi) < 184 or csi[:4] != b"ISTC":
        return None
    layout = struct.unpack_from("<H", csi, 36)[0]
    if layout != 12:
        return None
    width, height = struct.unpack_from("<2I", csi, 12)
    pixel_format = csi[24:28]
    # CSI stores the little-endian fourcc; premultiplied BGRA images carry the
    # raw bytes "BGRA" (displayed reversed as "ARGB" by readers).
    if pixel_format != b"BGRA":
        return None
    tlv_length, one, zero, payload_length = struct.unpack_from("<4I", csi, 168)
    payload = csi[184 + tlv_length: 184 + tlv_length + payload_length]
    if len(payload) != payload_length or len(payload) < 32 or payload[:4] != b"MLEC":
        return None
    mode, codec, flen, f1, bpp, dlen, zero2 = struct.unpack_from("<7I", payload, 4)
    if bpp != 4 or codec != 11:
        return None
    dmp2 = payload[32:32 + dlen]
    if len(dmp2) != dlen or dmp2[:4] != b"dmp2":
        return None
    version = dmp2[4]
    w2, h2 = struct.unpack_from("<HH", dmp2, 8)
    if (w2, h2) != (width, height):
        return None
    npix = width * height
    if version == 1:
        raw = dmp2[12:]
        return (width, height, bytes(raw)) if len(raw) == npix * 4 else None
    if version == 2:
        stream_length = struct.unpack_from("<H", dmp2, 12)[0]
        stream = dmp2[16:16 + stream_length]
        try:
            raw = lzfse_compat.decompress(stream)
        except ValueError:
            return None
        return (width, height, raw) if len(raw) == npix * 4 else None
    if version == 4:
        count, bppv = struct.unpack_from("<HH", dmp2, 12)
        if bppv != 4 or not 1 <= count <= 256:
            return None
        palette = dmp2[16:16 + 4 * count]
        stream_length = struct.unpack_from("<I", dmp2, 16 + 4 * count)[0]
        stream = dmp2[20 + 4 * count: 20 + 4 * count + stream_length]
        try:
            indices = lzfse_compat.decompress(stream)
        except ValueError:
            return None
        if len(indices) != npix:
            return None
        out = bytearray(npix * 4)
        for i, idx in enumerate(indices):
            if idx >= count:
                return None
            out[4 * i:4 * i + 4] = palette[4 * idx:4 * idx + 4]
        return width, height, bytes(out)
    return None


def is_pack_candidate(asset: AssetRendition) -> bool:
    if asset.skip_facet or asset.identifier_override == 0:
        return False
    if asset.part != 181 or asset.effective_facet_part != 181 or asset.element != 85:
        return False
    if asset.scale != 1 or asset.idiom != 0 or asset.appearance not in (0, 1, 2):
        return False
    if asset.localization is not None or asset.subtype or asset.layer:
        return False
    if asset.dimension1 or asset.dimension2 or asset.glyph_weight or asset.glyph_size:
        return False
    if asset.state or asset.direction or asset.atlas_linked:
        return False
    return _decode_deepmap_bgra(asset.csi) is not None


def _shelf_pack(rects: list[tuple[int, int]]) -> tuple[list[tuple[int, int]], int, int]:
    """Deterministic shelf packing with 2px padding, tallest first.

    Returns (positions, width, height). Shelf packing differs from Apple's
    private bin packer; LINK offsets stay internally consistent.
    """
    order = sorted(range(len(rects)), key=lambda i: (-rects[i][1], -rects[i][0]))
    pad = ATLAS_PADDING
    total = sum((w + pad) * (h + pad) for w, h in rects)
    max_w = max(w for w, _ in rects) + pad
    target = max(max_w, int(total ** 0.5) + 1)
    positions = [(0, 0)] * len(rects)
    x = y = pad
    shelf_h = 0
    max_x = max_y = 0
    for i in order:
        w, h = rects[i]
        if shelf_h and x + w + pad > target:
            x = pad
            y += shelf_h + pad
            shelf_h = 0
        positions[i] = (x, y)
        x += w + pad
        shelf_h = max(shelf_h, h)
        max_x = max(max_x, positions[i][0] + w)
        max_y = max(max_y, positions[i][1] + h)
    if not rects:
        return positions, 0, 0
    return positions, max_x + pad, max_y + pad


def _atlas_dmp2(width: int, height: int, bgra: bytes) -> bytes:
    """dmp2 v4 when the atlas uses <=256 colors, else v2 raw BGRA LZFSE."""
    colors: dict[bytes, int] = {}
    indices = bytearray(width * height)
    for i in range(width * height):
        px = bytes(bgra[4 * i:4 * i + 4])
        idx = colors.get(px)
        if idx is None:
            if len(colors) >= 256:
                break
            idx = len(colors)
            colors[px] = idx
        indices.append(idx)
    if len(colors) <= 256:
        # Swatch order: transparent padding first, then first-occurrence in
        # row-major scan order (observed padding swatch rule).
        swatches = [bytes(4)] + [c for c in colors if c != bytes(4)]
        remapped = {c: n for n, c in enumerate(swatches)}
        plane = bytes(remapped[bytes(bgra[4 * i:4 * i + 4])] for i in range(width * height))
        stream = lzfse_compat.compress(plane)
        return (b"dmp2" + bytes((4, 1, 10, 4)) + struct.pack("<HHHH", width, height, len(swatches), 4)
                + b"".join(swatches) + struct.pack("<I", len(stream)) + stream)
    stream = lzfse_compat.compress(bgra)
    return (b"dmp2" + bytes((2, 1, 10, 4)) + struct.pack("<HH", width, height)
            + struct.pack("<HH", len(stream), 0) + stream)


def _csi_atlas(width: int, height: int, bgra: bytes) -> bytes:
    dmp2 = _atlas_dmp2(width, height, bgra)
    payload = b"MLEC" + struct.pack("<7I", 2, 11, 16 + len(dmp2), 1, 4, len(dmp2), 0) + dmp2
    stride = (width * 4 + 15) // 16 * 16
    tlvs = b"".join((
        struct.pack("<2I5I", 1001, 20, 1, 0, 0, 0, 0),
        struct.pack("<2I8s", 1004, 8, b"\0\0\0\0\0\0\x80?"),
        struct.pack("<2II", 1006, 4, 1),
        struct.pack("<2II", 1007, 4, stride),
    ))
    header = bytearray(184)
    header[:4] = b"ISTC"
    struct.pack_into("<5I", header, 4, 1, 0, width, height, 100)
    header[24:28] = b"BGRA"
    struct.pack_into("<I", header, 28, 1)
    struct.pack_into("<I2H", header, 32, 0, 1004, 0)
    header[40:168] = _fixed(PACKED_ASSET_NAME, 128)
    struct.pack_into("<4I", header, 168, len(tlvs), 1, 0, len(payload))
    return bytes(header) + tlvs + payload


def _link_tail(appearance: int) -> bytes:
    """TLV-1010 key stream: pairs (1,9)(2,181)(12,1)[(7,appearance)](0,0)."""
    pairs = [(1, 9), (2, 181), (12, 1)]
    if appearance:
        pairs.append((7, appearance))
    pairs.append((0, 0))
    body = b"".join(struct.pack("<2H", a, v) for a, v in pairs)
    return struct.pack("<3H", 12, 4 * len(pairs), 0) + body


def _csi_link(source_csi: bytes, x: int, y: int, width: int, height: int, appearance: int) -> bytes:
    tlv_length, one, zero, payload_length = struct.unpack_from("<4I", source_csi, 168)
    out = bytearray(source_csi[:184])
    struct.pack_into("<H", out, 36, 1003)
    link = (_LINK_MAGIC + struct.pack("<5I", 0, x, y, width, height) + _link_tail(appearance))
    # Rebuild the TLV section in the observed order: keep 1001 and 1003,
    # insert 1010 right after 1003, then 1004/1006; drop 1007 (row bytes).
    head_tlvs = source_csi[184:184 + tlv_length]
    rebuilt = bytearray()
    cursor = 0
    while cursor + 8 <= len(head_tlvs):
        tag, length = struct.unpack_from("<2I", head_tlvs, cursor)
        if tag == 1007:
            cursor += 8 + length
            continue
        rebuilt += head_tlvs[cursor:cursor + 8 + length]
        cursor += 8 + length
        if tag == 1003:
            rebuilt += struct.pack("<2I", 1010, len(link)) + link
    struct.pack_into("<4I", out, 168, len(rebuilt), 1, 0, 0)
    return bytes(out) + bytes(rebuilt)


def pack_renditions(assets: list[AssetRendition]) -> list[AssetRendition]:
    """Replace packable rendition pixel data with LINK references + atlases.

    Callers must only invoke this when the catalog emits an appearance or
    localization registry (observed master switch).
    """
    candidates = [a for a in assets if is_pack_candidate(a)]
    by_appearance: dict[int, list[AssetRendition]] = {}
    for asset in candidates:
        by_appearance.setdefault(asset.appearance, []).append(asset)
    packed_appearances = {app for app, group in by_appearance.items() if len(group) >= 2}
    if not packed_appearances:
        return list(assets)

    result = list(assets)
    index_of = {id(a): i for i, a in enumerate(result)}
    atlases: list[AssetRendition] = []
    for appearance in sorted(packed_appearances):
        group = by_appearance[appearance]
        decoded = [_decode_deepmap_bgra(a.csi) for a in group]
        assert all(d is not None for d in decoded)
        rects = [(d[0], d[1]) for d in decoded]  # type: ignore[index]
        positions, atlas_w, atlas_h = _shelf_pack(rects)
        canvas = bytearray(atlas_w * atlas_h * 4)
        for (x, y), (w, h, pixels) in zip(positions, decoded):
            for row in range(h):
                src = row * w * 4
                dst = ((y + row) * atlas_w + x) * 4
                canvas[dst:dst + w * 4] = pixels[src:src + w * 4]  # type: ignore[index]
        atlas_csi = _csi_atlas(atlas_w, atlas_h, bytes(canvas))
        atlases.append(AssetRendition(
            PACKED_ASSET_NAME, atlas_csi, 181, 181, scale=1, idiom=0,
            appearance=appearance, element=9, identifier_override=0, skip_facet=True,
        ))
        for asset, (x, y), (w, h, _pixels) in zip(group, positions, decoded):
            link_csi = _csi_link(asset.csi, x, y, w, h, appearance)  # type: ignore[index]
            result[index_of[id(asset)]] = replace(asset, csi=link_csi)
    return result + atlases
