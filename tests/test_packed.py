"""Tests for the CoreUI packed-asset (ZZZZPackedAsset / LINK) writer."""
import base64
import binascii
import struct
import unittest
import zlib

from actool_linux.bom import BOMStore
from actool_linux.car import CARFile
from actool_linux.carwriter import build_assets_car, png_rendition
from actool_linux import lzfse_compat
from actool_linux.packed import pack_renditions, is_pack_candidate, _shelf_pack


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)


def _png_rgba(w: int, h: int, rgba) -> bytes:
    raw = (b"\x00" + bytes(rgba) * w) * h
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))


def _png_gray(w: int, h: int, v: int) -> bytes:
    raw = (b"\x00" + bytes((v,)) * w) * h
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))


def _write_car(tmp, rends):
    from pathlib import Path
    p = Path(tmp) / "Assets.car"
    p.write_bytes(build_assets_car(rends, platform="iphoneos", target="15.0"))
    return CARFile(BOMStore.from_path(p))


class PackedAssetTests(unittest.TestCase):
    def _candidates(self):
        return [
            png_rendition("Multi", _png_rgba(16, 16, (30, 100, 200, 255)), "img1x.png", scale=1),
            png_rendition("Multi", _png_rgba(32, 32, (30, 100, 200, 255)), "img2x.png", scale=2),
            png_rendition("Variant", _png_rgba(8, 8, (1, 2, 3, 255)), "any.png", scale=1),
            png_rendition("Variant", _png_rgba(8, 8, (4, 5, 6, 255)), "dark.png", scale=1, appearance=1),
        ]

    def test_candidate_predicate(self):
        rends = self._candidates()
        flags = [is_pack_candidate(r) for r in rends]
        self.assertEqual(flags, [True, False, True, True])  # 2x scale excluded

    def test_atlas_and_links_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            car = _write_car(tmp, self._candidates())
        layouts = {r.csi.layout for r in car.renditions}
        self.assertIn(1004, layouts)
        self.assertIn(1003, layouts)
        atlas = next(r for r in car.renditions if r.csi.layout == 1004)
        # atlas key: identifier 0, element 9, part 181, scale 1, appearance 0
        self.assertEqual((atlas.key["kCRThemeIdentifierName"], atlas.key["kCRThemeElementName"],
                          atlas.key["kCRThemePartName"], atlas.key["kCRThemeScaleName"],
                          atlas.key["kCRThemeAppearanceName"]), (0, 9, 181, 1, 0))
        self.assertEqual(atlas.csi.name, "ZZZZPackedAsset-1.1.0-gamut0")
        self.assertEqual(atlas.csi.pixel_format, "ARGB")
        self.assertEqual((atlas.csi.flags, [t.tag for t in atlas.csi.tlvs]), (0, [1001, 1004, 1006, 1007]))
        # no facet record for the atlas
        self.assertNotIn("ZZZZPackedAsset-1.1.0-gamut0", [f.name for f in car.facets])
        # decode atlas v4 palette and confirm swatch 0 is transparent
        pl = atlas.csi.rendition_data
        self.assertEqual(pl[:4], b"MLEC")
        mode, codec, _flen, _f1, bpp, dlen, _z = struct.unpack_from("<7I", pl, 4)
        self.assertEqual((mode, codec, bpp), (2, 11, 4))
        dmp2 = pl[32:32 + dlen]
        self.assertEqual(dmp2[4], 4)  # palette grammar
        n, _ = struct.unpack_from("<HH", dmp2, 12)
        pal = dmp2[16:16 + 4 * n]
        self.assertEqual(tuple(pal[:4]), (0, 0, 0, 0))
        self.assertIn((200, 100, 30, 255), [tuple(pal[4 * i:4 * i + 4]) for i in range(n)])
        # LINK renditions: both 1x facets link into the atlas
        links = {}
        for r in car.renditions:
            if r.csi.layout != 1003:
                continue
            t = next(t for t in r.csi.tlvs if t.tag == 1010)
            _m, _r, x, y, w, h = struct.unpack_from("<4s5I", t.value, 0)
            links[r.csi.name] = (x, y, w, h)
            self.assertEqual(t.value[:4], bytes.fromhex("4b4c4e49"))
            self.assertEqual((r.csi.flags, len(r.csi.rendition_data or b"")), (16, 0))
            self.assertEqual([tt.tag for tt in r.csi.tlvs], [1001, 1003, 1010, 1004, 1006])
        self.assertEqual(set(links), {"img1x.png", "any.png"})
        self.assertEqual(links["img1x.png"][2:], (16, 16))
        self.assertEqual(links["any.png"][2:], (8, 8))
        # every LINK rect fits inside the atlas and regions do not overlap
        aw, ah = atlas.csi.width, atlas.csi.height
        boxes = list(links.values())
        for x, y, w, h in boxes:
            self.assertTrue(0 <= x and 0 <= y and x + w <= aw and y + h <= ah)
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                self.assertFalse(a[0] < b[0] + b[2] and b[0] < a[0] + a[2]
                                 and a[1] < b[1] + b[3] and b[1] < a[1] + a[3])
        # decode the atlas plane and verify pixel colors at LINK rects
        (slen,) = struct.unpack_from("<I", dmp2, 16 + 4 * n)
        plane = lzfse_compat.decompress(dmp2[20 + 4 * n:20 + 4 * n + slen])
        x, y, w, h = links["img1x.png"]
        idx = plane[(y + 1) * aw + x + 1]
        self.assertEqual(tuple(pal[4 * idx:4 * idx + 4]), (200, 100, 30, 255))
        x, y, w, h = links["any.png"]
        idx = plane[(y + 1) * aw + x + 1]
        self.assertEqual(tuple(pal[4 * idx:4 * idx + 4]), (3, 2, 1, 255))

    def test_single_candidate_appearance_is_not_packed(self):
        import tempfile
        rends = [
            png_rendition("A", _png_rgba(32, 32, (1, 100, 200, 255)), "any.png", scale=1),
            png_rendition("A", _png_rgba(32, 32, (2, 100, 200, 255)), "dark.png", scale=1, appearance=1),
            png_rendition("B", _png_rgba(8, 8, (9, 8, 7, 255)), "b.png", scale=1),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            car = _write_car(tmp, rends)
        # appearance 0 has two candidates -> packed; appearance 1 has one -> stays layout 12
        app1 = next(r for r in car.renditions if r.key["kCRThemeAppearanceName"] == 1)
        self.assertEqual(app1.csi.layout, 12)
        layouts = [r.csi.layout for r in car.renditions]
        self.assertEqual(layouts.count(1004), 1)
        self.assertEqual(layouts.count(1003), 2)

    def test_grayscale_is_never_packed(self):
        import tempfile
        rends = [
            png_rendition("G", _png_gray(8, 8, 90), "any.png", scale=1),
            png_rendition("G", _png_gray(8, 8, 200), "dark.png", scale=1, appearance=1),
            png_rendition("H", _png_gray(8, 8, 33), "h.png", scale=1),
            png_rendition("H", _png_gray(8, 8, 44), "hd.png", scale=1, appearance=1),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            car = _write_car(tmp, rends)
        self.assertNotIn(1004, {r.csi.layout for r in car.renditions})
        self.assertTrue(all(r.csi.pixel_format == "GA8 " for r in car.renditions))

    def test_no_registry_no_packing(self):
        import tempfile
        rends = [
            png_rendition("A", _png_rgba(16, 16, (1, 2, 3, 255)), "a.png", scale=1),
            png_rendition("B", _png_rgba(16, 16, (4, 5, 6, 255)), "b.png", scale=1),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            car = _write_car(tmp, rends)
        self.assertNotIn(1004, {r.csi.layout for r in car.renditions})

    def test_shelf_pack_deterministic_and_padded(self):
        rects = [(16, 16), (8, 8), (32, 32)]
        positions, w, h = _shelf_pack(rects)
        self.assertEqual(w, 36)
        self.assertEqual(positions[2], (2, 2))  # tallest first
        self.assertEqual(h, 54)                 # second shelf below the 32px row
        # deterministic: same input -> identical layout
        self.assertEqual(_shelf_pack(rects), (positions, w, h))

    def test_pack_renditions_preserves_non_candidates(self):
        ga = png_rendition("G", _png_gray(8, 8, 90), "g.png", scale=1)
        two_x = png_rendition("M", _png_rgba(16, 16, (1, 2, 3, 255)), "m2.png", scale=2)
        out = pack_renditions([ga, two_x])
        self.assertEqual([id(a) for a in out], [id(ga), id(two_x)])


if __name__ == "__main__":
    unittest.main()
