# Module: `bomwriter`\n\n## Classes\n### `PendingBlock`\n\n### `BOMWriter`\nDeterministic writer for the generic BOMStore container layer.

This layer knows nothing about CoreUI payloads. Blocks are allocated in
insertion order, payloads are 16-byte aligned, and index capacity is a
power of two. All container metadata is big-endian as required by BOM.\n\n**Methods:**\n- `__init__()`\n- `add_block()`\n- `_align()`\n- `replace_block()`\n- `build()`\n\n