# Module: `atlas_geometry`\n\n## Overview\nImproved atlas packing geometry for better Apple compatibility.

This module provides enhanced packing algorithms that more closely match
Apple's actool behavior, particularly for edge cases with different
aspect ratios and sizes.\n\n## Public Functions\n### `improved_shelf_pack()`\nImproved shelf packing algorithm that better matches Apple's behavior.

Args:
    rects: List of (width, height) tuples
    max_width: Maximum atlas width
    max_height: Maximum atlas height

Returns:
    Tuple of (positions, atlas_width, atlas_height)
    where positions is a list of (x, y) tuples\n\n### `apple_style_pack()`\nApple-style packing that prioritizes area efficiency and aspect ratio.

This algorithm more closely matches Apple's observed behavior:
1. Sort by area (largest first)
2. Use skyline algorithm for placement
3. Prefer square-ish final atlas dimensions
4. Align to 4-pixel boundaries when possible\n\n### `calculate_packing_efficiency()`\nCalculate the packing efficiency (used area / total area).\n\n