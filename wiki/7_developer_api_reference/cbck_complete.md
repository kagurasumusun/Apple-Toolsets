# Module: `cbck_complete`\n\n## Overview\nComplete CBCK (Chunked Bitmap Compression) implementation.

This module provides a complete implementation of Apple's CBCK format,
which is used for compressing bitmap data in CAR files.\n\n## Classes\n### `CBCKChunk`\nA single CBCK chunk containing compressed bitmap data.\n\n**Methods:**\n- `__init__()`\n- `from_raw()`\n- `_compress_pixels()`\n- `decompress()`\n\n### `CBCKEncoder`\nEncoder for CBCK format with chunk size optimization.\n\n**Methods:**\n- `__init__()`\n- `determine_optimal_chunk_size()`\n- `_align_to_power_of_2()`\n- `encode()`\n- `_extract_chunk()`\n- `calculate_compression_ratio()`\n\n### `CBCKDecoder`\nDecoder for CBCK format.\n\n**Methods:**\n- `decode()`\n\n## Public Functions\n### `optimize_cbck_for_apple_compatibility()`\nOptimize CBCK encoding for maximum Apple compatibility.

This function applies Apple-specific optimizations:
1. Chunk size alignment to match Apple's preferences
2. Compression parameter tuning
3. Metadata generation

Returns:
    Tuple of (encoded_data, metadata)\n\n