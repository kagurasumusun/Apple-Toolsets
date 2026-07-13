from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .bom import BOMError, BOMStore
from .car import CARFile


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
                "tlvs": [
                    {"tag": tlv.tag, "length": len(tlv.value)}
                    for tlv in rendition.csi.tlvs
                ],
                "payload_length": len(rendition.csi.rendition_data),
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
