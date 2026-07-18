# Module: `zero_code_db`\n\n## Overview\nZero-code database support for CoreUI 850+.

This module provides support for zero-code bezel and glyph databases,
which are used in CoreUI 850+ for rendering UI elements without
requiring bitmap assets.\n\n## Classes\n### `ZeroCodeBezel`\nA zero-code bezel definition.

Zero-code bezels define UI elements (buttons, panels, etc.) using
vector graphics and procedural rendering instead of bitmaps.\n\n**Methods:**\n- `__init__()`\n- `add_layer()`\n- `add_effect()`\n- `serialize()`\n- `deserialize()`\n\n### `ZeroCodeLayer`\nA layer in a zero-code bezel.\n\n**Methods:**\n- `__init__()`\n- `set_property()`\n- `serialize()`\n- `deserialize()`\n\n### `ZeroCodeEffect`\nAn effect applied to a zero-code bezel.\n\n**Methods:**\n- `__init__()`\n- `set_parameter()`\n- `serialize()`\n- `deserialize()`\n\n### `ZeroCodeGlyph`\nA zero-code glyph definition (for text rendering).\n\n**Methods:**\n- `__init__()`\n- `add_path()`\n- `serialize()`\n\n### `ZeroCodeDatabase`\nContainer for zero-code bezel and glyph databases.\n\n**Methods:**\n- `__init__()`\n- `add_bezel()`\n- `add_glyph()`\n- `get_bezel()`\n- `get_glyph()`\n- `serialize_bezels()`\n- `serialize_glyphs()`\n\n