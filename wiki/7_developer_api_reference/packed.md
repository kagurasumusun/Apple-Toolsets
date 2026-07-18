# Module: `packed`\n\n## Overview\nCoreUI packed-asset (ZZZZPackedAsset / LINK) writer.

Observed Apple behavior (Xcode 26.x oracles; derived only from observable
outputs on independently created input catalogs):

Apple replaces the pixel data of every scale-1, non-localized, universal-
idiom image rendition that shares a *packing class* with at least one other
such rendition (probe3/probe5 oracles):

- The rendition becomes layout 1003 with TLVs [1001, 1003, 1010, 1004, 1006]
  and an empty payload. TLV 1010 ("LINK") carries the (x, y, w, h) rectangle
  inside the atlas plus the key of the atlas rendition.
- Packing classes are ``(appearance, alpha-class, color-class)`` where
  alpha-class is "any pixel not fully opaque" and color-class is "every
  pixel has r == g == b" (grayscale or grayscale-representable RGB(A)).
  Atlases are named ``ZZZZPackedAsset-1.{opaque?1:0}.{gray?1:0}-gamut0`` and
  there is one atlas rendition per class. Sources are only packed when their
  class registers >= 2 candidates (verified threshold: 2 packs, 1 does not;
  no appearance/localization registry is required). Whether Apple also
  tests the bit-depth / premultiplied-input color space before classifying
  is unobserved.
- Atlas keys carry identifier=0, element=9, part=181, scale=1, appearance=A.
  When an appearance owns more than one atlas page the whole catalog's
  KEYFORMAT gains attribute 8 (dimension1) — (7,13,12,15,16,8,17,1,2) for
  iOS-family platforms, (7,13,1,2,3,17,8,11,12) for macosx — and the atlas
  page serial lives in dimension1, pages numbered in class-name order.
  LINK tails then reference the page with an (8, page) attribute pair
  (omitted for page 0). Multiple pages per class (Apple's bigint pagination
  heuristic) are not yet replicated: this writer emits one page per class,
  which matches every single-page oracle (documented cosmetic difference).
- Atlas payload: MLEC (mode 2 for opaque classes, 0 for alpha classes)
  codec 11 wrapping dmp2: palette grammar v4 for color atlases (<=255
  distinct colors + transparent padding swatch 0), raw LZFSE grammar v2
  for grayscale atlases or >255 colors. Pixels are premultiplied BGRA
  (v,a for grayscale); atlas padding is transparent.
- Non-1x scales, localized renditions, non-universal idioms and vector
  fallbacks are never packed.

The exact Apple bin-packing heuristic is private; this module uses a
deterministic shelf packer. Offsets written into LINK renditions always
match our own atlas, so consumer resolution is unaffected (documented
cosmetic difference).\n\n## Public Functions\n### `atlas_name()`\nAtlas rendition naming scheme observed in Xcode 26.5 oracles (may
change with CoreUI versions; keep in sync with probe oracles).\n\n### `is_pack_candidate()`\n\n### `composite_atlas()`\n\n### `pack_renditions()`\nReplace packable rendition pixels with LINK references + atlases.

Observed rule: candidates are scale-1, universal, non-localized image
renditions; a class ``(appearance, alpha-class, color-class)`` packs when
it has >= 2 candidates. No appearance/localization registry is required.\n\n