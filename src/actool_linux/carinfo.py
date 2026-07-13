from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .bom import BOMError, BOMStore
from .car import CARFile
from .atlas import parse_atlas_link, parse_atlas_name_list, parse_atlas_trim
from .paletteimg import decode_quantized_image_payload, parse_theme_pixel_rendition


def _decoded_tlvs(rendition) -> list[dict[str, object]]:
    rows = []
    for tlv in rendition.csi.tlvs:
        item: dict[str, object] = {"tag": tlv.tag, "length": len(tlv.value)}
        try:
            if tlv.tag == 1010:
                link = parse_atlas_link(tlv.value)
                item["atlas_link"] = {
                    "x": link.x,
                    "y": link.y,
                    "width": link.width,
                    "height": link.height,
                    "variant": link.variant,
                    "header_u16": link.header_u16,
                    "header_u32": link.header_u32,
                    "tokens": [{"attribute": t.attribute, "value": t.value} for t in link.tokens],
                }
            elif tlv.tag == 1011:
                trim = parse_atlas_trim(tlv.value)
                item["atlas_trim"] = trim.__dict__
            elif tlv.tag == 1013:
                item["atlas_name_list"] = list(parse_atlas_name_list(tlv.value).names)
        except Exception as exc:
            item["decode_error"] = str(exc)
        rows.append(item)
    return rows


def _decoded_payload(rendition) -> dict[str, object] | None:
    try:
        wrapper = parse_theme_pixel_rendition(rendition.csi.rendition_data)
    except Exception:
        return None
    result = {
        "wrapper_version": wrapper.version,
        "compression_type": wrapper.compression_type,
        "raw_payload_length": len(wrapper.raw_data),
    }
    if wrapper.compression_type == 8:
        try:
            decoded = decode_quantized_image_payload(wrapper.raw_data, width=rendition.csi.width, height=rendition.csi.height, pixel_format=rendition.csi.pixel_format)
            result["quantized"] = {
                "version": decoded.version,
                "palette_count": len(decoded.palette),
                "bits_per_index": decoded.bits_per_index,
                "decoded_indices": len(decoded.indices),
            }
        except Exception as exc:
            result["quantized_error"] = str(exc)
    return result


def inspect(path: Path) -> dict[str, object]:
    store = BOMStore.from_path(path)
    car = CARFile(store)
    return {
        "path": str(path),
        "size": path.stat().st_size,
        "bom_version": store.header.version,
        "block_count_hint": store.header.block_count_hint,
        "allocated_blocks": len(store.blocks),
        "car_header": {
            "byte_order": car.header.byte_order,
            "core_ui_version": car.header.core_ui_version,
            "storage_version": car.header.storage_version,
            "storage_timestamp": car.header.storage_timestamp,
            "schema_version": car.header.schema_version,
            "rendition_count": car.header.rendition_count,
            "main_version": car.header.main_version,
            "version_string": car.header.version_string,
            "identifier": car.header.identifier,
            "associated_checksum": car.header.associated_checksum,
            "color_space_id": car.header.color_space_id,
            "key_semantics": car.header.key_semantics,
        },
        "extended_metadata": (
            car.extended_metadata.__dict__ if car.extended_metadata else None
        ),
        "key_format": list(car.key_format.names),
        "facets": [
            {
                "name": facet.name,
                "cursor_hotspot": list(facet.cursor_hotspot),
                "attributes": facet.named_attributes,
            }
            for facet in car.facets
        ],
        "renditions": [
            {
                "name": rendition.csi.name,
                "width": rendition.csi.width,
                "height": rendition.csi.height,
                "scale": rendition.csi.scale,
                "pixel_format": rendition.csi.pixel_format,
                "color_space_id": rendition.csi.color_space_id,
                "layout": rendition.csi.layout,
                "flags": rendition.csi.flags,
                "key": rendition.key,
                "tlvs": _decoded_tlvs(rendition),
                "payload_length": len(rendition.csi.rendition_data),
                "decoded_payload": _decoded_payload(rendition),
            }
            for rendition in car.renditions
        ],
        "named_blocks": [
            {"name": name, "identifier": identifier, "size": len(store.block(identifier))}
            for name, identifier in store.variables.items()
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="actool-car-info")
    parser.add_argument("car", type=Path)
    ns = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(ns.car), indent=2))
    except (OSError, BOMError) as exc:
        print(f"actool-car-info: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
