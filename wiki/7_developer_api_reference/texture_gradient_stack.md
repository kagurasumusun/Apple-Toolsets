# Module: `texture_gradient_stack`\n\n## Overview\nComplete implementation of texture references, named gradients, and icon stacks.

This module provides full support for advanced CAR file features:
- Texture references (RTXT payloads)
- Named gradients (ARGG payloads)
- Icon stacks (layered icons with rendering properties)
from typing import any\n\n## Classes\n### `TextureReference`\nA texture reference pointing to external texture data.

RTXT payloads reference textures stored elsewhere in the CAR file
or in external resources.\n\n**Methods:**\n- `__init__()`\n- `add_key_pair()`\n- `serialize()`\n- `deserialize()`\n\n### `GradientStop`\nA color stop in a gradient.\n\n**Methods:**\n- `__init__()`\n- `serialize()`\n- `deserialize()`\n\n### `NamedGradient`\nA named gradient definition (ARGG payload).

Named gradients define reusable gradient fills that can be
referenced by name throughout the CAR file.\n\n**Methods:**\n- `__init__()`\n- `add_stop()`\n- `serialize()`\n- `deserialize()`\n\n### `IconStackLayer`\nA layer in an icon stack.\n\n**Methods:**\n- `__init__()`\n- `set_bounds()`\n- `add_referenced_key()`\n- `serialize()`\n- `deserialize()`\n\n### `IconStackRenderingProperties`\nRendering properties for an icon stack.\n\n**Methods:**\n- `__init__()`\n- `add_entry()`\n- `serialize()`\n- `deserialize()`\n\n### `IconStack`\nAn icon stack with multiple layers and rendering properties.

Icon stacks allow composing complex icons from multiple layers
with advanced rendering effects.\n\n**Methods:**\n- `__init__()`\n- `add_layer()`\n- `set_rendering_properties()`\n- `add_auxiliary_data()`\n- `serialize()`\n- `deserialize()`\n\n## Public Functions\n### `create_linear_gradient()`\nCreate a linear gradient with the given stops.\n\n### `create_radial_gradient()`\nCreate a radial gradient with the given stops.\n\n### `create_simple_icon_stack()`\nCreate a simple icon stack with stacked layers.\n\n