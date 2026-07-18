# Module: `carwriter`\n\n## Classes\n### `AssetRendition`\n**Methods:**\n- `effective_facet_part()`\n\n## Public Functions\n### `resize_png()`\nNearest-neighbour PNG resize used for deterministic AppIcon sidecars.\n\n### `make_deepmap_csi_variant()`\nDeepmap2 CSI using the grammar variants observed in Apple output.

- uniform RGB(A) sources: dmp2 (4,1,10,4) palette-swatch + 1bpp index
  plane (LZFSE), MLEC mode 2 for bottom-most opaque layers, else mode 0.
- varied RGB(A) sources: dmp2 (2,1,10,4) premultiplied-BGRA LZFSE stream,
  MLEC mode 0.
- oversized sources with prefer_cbck: MLEC mode 3 codec 11 KCBC chunks;
  each chunk carries its own field header + per-band dmp2.
- GA sources keep the original bounds-checked v1 grammar
  (already Apple consumer verified).\n\n### `png_dimensions()`\n\n### `build_assets_car()`\nBuild a CAR with any number of facets and renditions per facet.

Renditions sharing ``name`` share one FACETKEYS record and identifier. This
is required for ordinary 1x/2x/3x image sets. Duplicate CoreUI keys are
rejected because lookup would otherwise be ambiguous.\n\n### `build_pdf_fallback_car()`\n\n### `svg_renditions()`\nPreserve SVG and automatically rasterize deepmap fallbacks.\n\n### `build_svg_car()`\n\n### `cbck_png_rendition()`\nBuild an ordinary image rendition using chunked CBCK/LZFSE storage.\n\n### `layered_image_renditions()`\nCreate ordered CoreUI layer-key renditions for tvOS/visionOS image stacks.\n\n### `build_layered_icon_car()`\n\n### `solid_image_stack_aggregate_renditions()`\nExperimental aggregate-oriented SolidImageStack rendition set.

This models the currently observed public visionOS `solidimagestack` oracle:
one layout-1018 aggregate metadata rendition, ordinary image renditions for
each content layer, and texture-oriented 1007/1008 side renditions for two
dimension1 modes. The exact Apple writer is still more complex.\n\n### `build_solid_image_stack_aggregate_car()`\n\n### `watch_complication_renditions()`\nEncode watch family in subtype and role in dimension2 keys.\n\n### `build_watch_complication_car()`\n\n### `app_icon_renditions()`\nReturn platform-specific MSIS and CBCK records for a modern AppIcon.\n\n### `build_app_icon_car()`\n\n### `data_rendition()`\n\n### `jpeg_rendition()`\n\n### `heif_rendition()`\n\n### `png_rendition()`\n\n### `palette_png_rendition()`\nBuild a legacy quantized `palette-img` rendition from an indexed PNG input.\n\n### `symbol_template_renditions()`\nExpand SF Symbols template groups such as ``Regular-M`` into glyph records.\n\n### `build_symbol_template_car()`\n\n### `symbol_rendition()`\n\n### `build_symbol_car()`\n\n### `pdf_rendition()`\n\n### `build_data_car()`\n\n### `build_jpeg_car()`\n\n### `build_heif_car()`\n\n### `build_png_car()`\n\n### `build_palette_img_car()`\n\n### `build_pdf_car()`\n\n### `color_rendition()`\n\n### `build_color_car()`\n\n### `write_data_car()`\n\n### `write_jpeg_car()`\n\n### `write_heif_car()`\n\n### `write_color_car()`\n\n