# Module: `lzfse_optimized`\n\n## Overview\nOptimized LZFSE compression for better Apple compatibility.

This module provides enhanced LZFSE compression that more closely matches
Apple's implementation in terms of compression ratio and speed.\n\n## Classes\n### `LZFSEOptimized`\nOptimized LZFSE encoder with Apple-compatible parameters.\n\n**Methods:**\n- `__init__()`\n- `compress()`\n- `_compress_block()`\n- `_hash()`\n- `_find_match_length()`\n- `_encode_literals()`\n- `_encode_match()`\n- `_create_raw_block()`\n- `_create_empty_block()`\n- `_create_lzfse_stream()`\n\n## Public Functions\n### `compress_with_apple_compatibility()`\nCompress data with Apple-compatible LZFSE parameters.

This function uses parameters that closely match Apple's actool output.\n\n### `analyze_compression_ratio()`\nAnalyze compression efficiency.\n\n