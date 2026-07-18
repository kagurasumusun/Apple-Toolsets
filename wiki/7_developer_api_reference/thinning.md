# Module: `thinning`\n\n## Overview\nDeterministic CoreUI rendition thinning.

The selector operates on the clean-room intermediate representation, before BOM
indexes are emitted.  It deliberately retains universal/Any/unlocalized
fallbacks unless ``keep_fallbacks`` is disabled.\n\n## Classes\n### `ThinningOptions`\n**Methods:**\n- `idiom_id()`\n- `metadata_arguments()`\n\n## Public Functions\n### `thin_renditions()`\nSelect device-compatible renditions while preserving fallback records.

Vector payloads (part 42) and auxiliary records sharing the selected idiom
are retained. Ordering is unchanged; ``build_assets_car`` performs its own
canonical sort.\n\n