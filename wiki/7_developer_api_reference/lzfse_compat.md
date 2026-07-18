# Module: `lzfse_compat`\n\n## Overview\nSingle LZFSE entry point for the clean-room writer.

Every encoder/decoder in ``actool_linux`` goes through this module so the
project works in two modes:

1. Preferred: the optional third-party ``lzfse`` C extension (available on
   Linux and macOS via ``pip install lzfse``) provides the real encoder and
   decoder, byte-comparable with Apple platform output behaviour.
2. Fallback: a tiny built-in codec that emits *valid* LZFSE streams made only
   of uncompressed ``bvxn`` blocks terminated by the ``bvx-`` end-of-stream
   marker. Any conformant LZFSE decoder (including Apple's
   libcompression/CoreUI stack) accepts these blocks, so the CAR files remain
   fully readable by ``assetutil``/AppKit/UIKit; they are just larger than
   entropy-coded output.

The fallback decompressor decodes ``bvxn`` blocks (its own output) and raises
a clear error for entropy-coded ``bvx1``/``bvx2`` blocks, which need the C
extension. This keeps every failure explicit instead of silently truncating
upstream-produced streams.

Block layout (from the public LZFSE format description):

- ``bvxn`` u32 n_raw_bytes, u32 n_payload_bytes, then payload bytes
  (for uncompressed blocks n_raw_bytes == n_payload_bytes).
- ``bvx-`` end of stream.

Keeping this indirection in one module is deliberate: if Apple ships a new
compression codec in a future CoreUI, exactly one file changes.\n\n## Public Functions\n### `have_c_extension()`\n\n### `is_valid_stream()`\nCheap structural check usable without the C extension.\n\n### `compress()`\nCompress ``data`` to an LZFSE stream (never fails).\n\n### `decompress()`\nDecode an LZFSE stream.

With the C extension this decodes every valid stream. Without it, only
streams made of uncompressed blocks (as produced by :func:`compress` in
fallback mode) are supported.\n\n