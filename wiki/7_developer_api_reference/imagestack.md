# Module: `imagestack`\n\n## Overview\nClean-room writer for CoreUI layered image stack aggregates.

Reproduces the observable Apple actool output for `.imagestack` /
`.brandassets` sources on the tvOS path:

- layout-1002 root rendition ("Contents.json", DATA, public.layeredimage UTI)
  with TLV 1012 (layer reference list), TLV 1020 (stack flags), TLV 1021
  (auxiliary records), TLV 1004 (blend), TLV 1005 (UTI), TLV 1006.
- one deepmap2 child image per applicable layer, keyed to its own facet
  ("<stack>/<Layer>/Content").
- ZZZZFlattenedImage-1.1.0-gamut0 (part 208, layout 0) holding the
  source-over premultiplied BGRA composite as chunked CBCK/LZFSE.
- ZZZZRadiosityImage-1.0.0 (part 209, layout 0) holding the mode-0 light-map
  container: canvas padded by 40px per side, 32x16 px cell grid of u16 pairs
  preceded by the constant f32 0.7255510687828064 (baked opacity-scale).
  The exact Apple irradiance kernel is private; values here are an
  alpha-derived approximation (see RADIOITY_APPROXIMATION note).
- Top Shelf images compile as ordinary idiom-tv deepmap images.

Everything was derived from observable outputs of Apple actool on
independently created inputs; no Apple code is used.\n\n## Classes\n### `StackLayerImage`\n\n## Public Functions\n### `tlv_layer_list()`\nTLV 1012: header (count, reserved) + per-layer 32B fixed + 16B key.

entry: origin_x, origin_y, reserved0, width, height, reserved1, opacity,
       key_byte_length(16), key tokens (1,85)(2,181)(17,identifier)(0,0)\n\n### `tlv_stack_flags()`\nTLV 1020: header (count, reserved) + 13-byte flag records (enabled=1).\n\n### `tlv_stack_aux()`\nTLV 1021: header (count, reserved) + 20-byte zeroed auxiliary records.\n\n### `tlv_uti()`\n\n### `build_stack_root_csi()`\nlayout-1002 aggregate root rendition for a layered image stack.\n\n### `cbck_container()`\nMLEC mode-3 codec-4 chunked CBCK/LZFSE container.

Observed Apple flattened images always split into three KCBC chunks of
ceil(height/3) rows each.\n\n### `build_flattened_payload()`\n\n### `build_radiosity_payload()`\nMode-0 radiosity container.

Grammar (observed): MLEC, u32 mode=0, u32 codec=6, u32 data_length, then
u16 width, u16 height, u16 32, u16 0, f32 RADIOSITY_CONSTANT, and a
(width//32) x (height//16) cell-major grid of u16 pairs.

RADIOSITY_APPROXIMATION: the exact Apple irradiance values are private.
We emit an alpha-silhouette-derived smooth field: flat opaque icon
interior receives high values toward the lower third, edges fall off with
a 1-cell blur, producing the same shape family as observed fixtures
(bright lower band, fade to zero outside the silhouette).\n\n### `build_flattened_csi()`\n\n### `build_radiosity_csi()`\n\n### `imagestack_renditions()`\nBuild the full aggregate rendition family for one layered image stack.

`layers` must be ordered back-to-front (bottom-most first), matching the
observed TLV-1012 ordering. `root_identifier` overrides the aggregate
records' identifier (used for tvOS brandassets, where the marketing-size
stack reuses the primary stack's identifier).\n\n