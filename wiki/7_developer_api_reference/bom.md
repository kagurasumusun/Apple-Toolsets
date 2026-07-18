# Module: `bom`\n\n## Classes\n### `BOMError`\nRaised when a BOMStore container is malformed or unsupported.\n\n\n### `BOMHeader`\n\n### `Block`\n\n### `BOMStore`\nBounds-checked reader for the BOMStore container used by Assets.car.

BOM scalar metadata is big-endian. The payload of a named block may use a
different byte order and is intentionally left uninterpreted by this layer.\n\n**Methods:**\n- `__init__()`\n- `from_path()`\n- `_range()`\n- `_read_header()`\n- `_read_block_index()`\n- `_read_variables()`\n- `block()`\n- `named_block()`\n- `get_databases()`\n- `has_database()`\n\n