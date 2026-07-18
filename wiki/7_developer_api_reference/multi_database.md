# Module: `multi_database`\n\n## Overview\nMultiple BOM database support for legacy CoreUI compatibility.

This module provides support for reading and writing CAR files with
multiple specialized BOM databases, as used in older CoreUI versions.\n\n## Classes\n### `MultiDatabaseCAR`\nCAR file with multiple BOM databases.

Older CoreUI versions (< 700) use a single BOMStore, while newer
versions (700+) may use multiple specialized databases:
- imagedb: Image renditions
- colordb: Color definitions
- fontdb: Font definitions
- fontsizedb: Font size definitions
- appearancedb: Appearance definitions
- facetKeysdb: Facet keys (theme identifiers)
- bitmapKeydb: Bitmap keys
- zcbezeldb: Zero-code bezel database
- zcglyphdb: Zero-code glyph database\n\n**Methods:**\n- `__init__()`\n- `from_path()`\n- `get_database()`\n- `has_database()`\n- `get_all_databases()`\n- `get_image_renditions()`\n- `get_color_definitions()`\n- `get_facet_keys()`\n- `write_multi_database_car()`\n- `validate_compatibility()`\n\n