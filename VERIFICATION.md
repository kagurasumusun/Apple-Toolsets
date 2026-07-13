# Verification report

Primary environment: macOS 15.7.7 (24G720), Xcode 16.4 (16F6), CoreUI 918.5. Additional installed Xcodes exercised: 16.0–16.4 and 26.0.1–26.3 (including app aliases), with CoreUI 917/918/971/972 observations.

## Passing checks

- 34 unit tests on Linux and macOS.
- Apple `actool` oracle fixture: basic image CAR, 1 facet / 1 rendition.
- Stress oracle fixture: 300 facets / 301 renditions.
- Reader agreement with `assetutil`: CoreUI/storage/schema versions, main version, platform, deployment target, key format, facet names, rendition names, dimensions, and scales.
- Linux deterministic BOM writer repacks an Apple CAR; `assetutil` accepts the rewritten container.
- Linux CLI independently compiles one `.dataset` into `Assets.car`.
  - `assetutil`: name `Blob`, UTI `public.plain-text`, length 15.
  - AppKit `NSDataAsset`: loaded `hello-linux-car` from a bundle.
- Linux CLI independently compiles JPEG and HEIF/HEIC `.imageset` inputs into `Assets.car`.
  - `assetutil`: expected JPEG/HEIF encoding and 1×1 dimensions.
  - AppKit app-bundle executables: `NSImage(named:)` loaded both and produced 9400-byte TIFF representations.
- Linux CLI independently compiles sRGB and Display P3 `.colorset` inputs.
  - `assetutil`: expected colorspace and RGBA components.
  - AppKit `NSColor(named:bundle:)`: Display P3 RGBA `0.1/0.2/0.3/0.8` loaded unchanged.
- Preserved-PDF CSI/RAWD plus GA8 deepmap bitmap fallbacks at 1×/2×/optional-3× are emitted in one facet. iOS SDK `assetutil` recognized scales 1/2/3 plus vector, and AppKit `NSImage(named:)` loaded the Linux-generated CAR (`1×1`, TIFF length 29820). `actool-pdf-car` accepts pre-rasterized fallback PNGs; automatic PDF rasterization remains an optional-backend task.
- Independent `MLEC/dmp2` GA8 writer: arbitrary-size non-interlaced 8-bit grayscale-alpha PNG, filters 0–4, CRC/deflate validation, and premultiplied gray. Oracle payloads matched at 1×1, 2×1, 1×2, 2×2, 3×2 and 10×10. Apple `assetutil` and AppKit passed.
- Independent RGBA/ARGB dmp2 writer: RGBA input is alpha-premultiplied and stored BGRA. Oracle payloads matched at 1×1, 2×1 and 2×2. AppKit loaded the 2×2 image (TIFF length 6756).
- Independent opaque RGB writer: stores B,G,R,FF with dmp2 bpp=4 and opaque CLEM mode. Oracle matched at 1×1/2×2; `assetutil` and AppKit passed.
- Indexed PNG input at bit depth 1/2/4/8: PLTE/tRNS parsing, packed-index expansion, then verified ARGB dmp2 emission. `assetutil` and AppKit passed. A 24-case palette matrix (Xcode 16.0/16.4/26.3 × 2/16/64/256 px × opaque/tRNS) selected deepmap2/ARGB in every case; installed Xcodes never emitted legacy palette-img.
- 16-bit grayscale-alpha PNG: PNG unfilter operates at 4 bytes/pixel, Xcode-compatible high-byte quantization to GA8, then premultiplication. Oracle matched at 1×1/2×1/2×2; `assetutil` and AppKit passed at 2×2.
- Linux CLI emits multiple mixed assets and variable-length names in one CAR.
  - `assetutil`: `Color/Color`, `DataA/Data`, `Photo/Image`.
  - One AppKit process loaded `mixed-data`, the 1×1 image, and RGB `0.1/0.2/0.3` from that CAR.
- Installed-Xcode oracle matrix covered 20 Xcode app bundles/aliases and five SDK families (macOS, iOS, tvOS, watchOS, visionOS): 100 rows total, 60 successful Apple `actool` builds. Most failures were old-Xcode/runtime build-version mismatches; two visionOS builds timed out.
- The Linux-generated mixed CAR was opened successfully by `assetutil` in all 100 Xcode×SDK consumer combinations, spanning CoreUI 918, 971 and 972 families.
- CLI contract capture covered all 20 Xcode app bundles: help output had one common SHA-256, and unknown-option/no-input cases consistently exited 1.
- Optional LZFSE indexed-palette writer verified on macOS 26.4 / Xcode 26.5: `bvx2` stream, assetutil deepmap2/ARGB 64×64 SizeOnDisk 630, AppKit TIFF length 31268.

## Implemented format layers

- Asset catalog discovery and `Contents.json` parsing.
- BOMStore header, block index, variables and bounds validation.
- BOM leaf-tree descriptors and entries.
- CARHEADER, EXTENDED_METADATA, KEYFORMAT and FACETKEYS.
- CSI headers, rendition keys, TLVs and RAWD payloads.
- Deterministic BOM writer and CAR repacker.
- Independent RAWD data/JPEG and COLR named-color rendition writers.

## Not yet complete

Legacy palette-img, interlaced PNG, complete SVG fallback generation, appearance-varying colors, app icons, launch images, symbols, localization, general scale/idiom variants, multi-level B+ trees, thinning semantics, Simulator-app runtime tests, and the full `actool` option/diagnostic contract remain incomplete.

No claim of 100% compatibility should be made until those matrix entries pass real Apple consumers.

## Git

Commits were created on `main`. Push was attempted but GitHub returned HTTP 403 because the available `github-actions[bot]` credential has no write permission to `kagurasumusun/mac`.
