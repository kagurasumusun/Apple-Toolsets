# Engineering audit log

This is a reproducible engineering record, not a private chain-of-thought transcript.

## 2026-07-12 — CoreUI/BOM/CAR baseline

- Identified BOMStore container, block index, named variables and leaf trees.
- Implemented bounds checks, CARHEADER, KEYFORMAT, FACETKEYS, CSI/TLV parsing.
- Repacked an Apple CAR on Linux; Apple `assetutil` accepted it.

## Independent renditions

- RAWD data: `assetutil` and `NSDataAsset` passed.
- JPEG RAWD: `assetutil` and `NSImage` passed.
- HEIF RAWD: ISO BMFF `ftyp`/`ispe` parser; `assetutil` and `NSImage` passed.
- COLR sRGB and Display P3: `assetutil` and `NSColor` passed.
- Mixed multi-asset CAR: data/JPEG/color loaded in one AppKit process.

## Multi-Xcode matrix

- 20 installed Xcode app bundles/aliases, five SDK families, 100 rows.
- Apple actool oracle: 60 passes; failures were mostly old-runtime build mismatch; two xros timeouts.
- Linux mixed CAR consumer matrix: 100/100 `assetutil` passes across Xcode 16/26 and macOS/iOS/tvOS/watchOS/visionOS SDKs.
- actool contract: common help hash in observed installs; unknown/no-input exit 1.

## PDF/vector

Observed Xcode preserved-vector asset as three renditions:

1. PDF vector: pixel format `PDF `, layout 9, flags 4, rendition part 42.
2. GA8/deepmap2 bitmap fallback at 1×, image part 181.
3. GA8/deepmap2 bitmap fallback at 2×, image part 181.

A Linux vector-only CAR passed `assetutil` but not AppKit lookup. After adding part-42 PDF plus part-181 GA8 deepmap fallbacks at scale 1/2, the Linux CAR passed `assetutil` and AppKit (`NSImage`, TIFF length 29820). Optional scale 3 was then added and recognized by iOS SDK `assetutil` alongside scales 1/2 and vector. The dedicated `actool-pdf-car` command accepts pre-rasterized fallback PNGs.

## PNG/deepmap2 verified GA8 subset

Input constraint: non-interlaced, 8-bit grayscale-alpha PNG. General width/height supported with PNG filters 0–4.

Observed and reproduced rendition:

- CSI pixel format `GA8 `, layout 12, flags 16.
- `MLEC` envelope version 2.
- inner codec magic `dmp2`.
- little-endian width/height in dmp2 header.
- pixel bytes are premultiplied grayscale and alpha: `(gray * alpha + 127) // 255`.
- oracle matches recorded for 1×1, 2×1, 1×2, 2×2, 3×2 and 10×10.

Exact payload for black/opaque fixture:

```text
4d4c4543020000000b0000001e00000001000000020000000e00000000000000
646d703201010a020100010000ff
```

Validation:

- Apple `assetutil`: `Compression=deepmap2`, `Encoding=Gray`, 1×1.
- AppKit `NSImage(named:)`: 1×1 and TIFF representation generated.

RGBA rule was subsequently identified: premultiply each RGB channel, store bytes in BGRA order, use dmp2 bpp=4 and CSI format ARGB. Opaque RGB uses B,G,R,FF and CLEM mode 2. Indexed PNG depth 1/2/4/8 is expanded via PLTE/tRNS to ARGB dmp2. 16-bit GA uses the high byte of each sample before GA8 premultiplication. Oracle and AppKit passed these paths at 2×2. Palette probe: Xcode 16.0/16.4/26.3, sizes 2/16/64/256, opaque/tRNS — all 24 outputs were deepmap2/ARGB; no installed Xcode emitted legacy palette-img.

Large indexed dmp2 payloads contain palette metadata followed by an LZFSE `bvx2` stream. The stream was decompressed on Linux to the full 65536-byte index plane. The optional `lzfse>=0.4` writer backend emits palette BGRA + compressed index streams. Apple validation on macOS 26.4 / Xcode 26.5: `bvx2` at offset 68, `assetutil` reported deepmap2/ARGB 64×64 SizeOnDisk 630, and AppKit `NSImage(named:)` loaded it with TIFF length 31268.

## Git push

Repeated `git push origin main` attempts returned HTTP 403 for `github-actions[bot]`. The workflow token needs `permissions: contents: write` or another write-capable credential.

## 2026-07-13 — Adam7 and same-facet multi-scale deepmap milestone

### Implementation
- Added bounds-checked Adam7 pass reconstruction for supported PNG inputs.
- Each pass is independently unfiltered with PNG filters 0–4; empty passes are omitted as required by the PNG specification.
- Interlaced 8-bit RGB/GA/RGBA, 16-bit GA, and indexed 1/2/4/8-bit inputs now feed the existing verified deepmap2 writer.
- Generalized `build_assets_car` so several renditions can share one facet name and stable identifier.
- Added 1x/2x/3x scale selection to PNG/JPEG/HEIF rendition constructors and synchronized CSI scale and rendition key scale.
- Duplicate CoreUI rendition keys and inconsistent facet parts are rejected.

### Reproducible tests
- Linux unit suite: `PYTHONPATH=src python -m unittest discover -s tests -q` → 36 tests, OK.
- Apple host: macOS 26.4 (25E246), Xcode 26.5 (17F42).
- Linux-generated mixed CAR contained Adam7 3×3 and a single `Logo` facet with 1× and 2× deepmap renditions.
- `xcrun --sdk macosx assetutil --info` recognized all three as `Compression: deepmap2`, with Logo scale values 1 and 2.
- AppKit main-bundle consumer output:
  - `APPLE_CONSUMER_PASS Adam7 3 3 6796`
  - `APPLE_CONSUMER_PASS Logo 1 1 9458`

### Boundary
This validates CAR parsing and AppKit consumption on the stated Apple host. It does not yet establish byte-identical actool output, idiom/appearance selection, legacy palette-img, packed atlas, or Simulator coverage.

## 2026-07-13 — Multi-level BOM B+ tree and AppIcon oracle

### Multi-level tree oracle
- Generated 5,000 independent image facets with Xcode 26.5 `actool` on macOS 26.4.
- Apple output: 2.6 MiB CAR; RENDITIONS root type 0 with 15 separators and 16 children; FACETKEYS root type 0 with 18 separators and 19 children.
- Confirmed internal representation: header `>HHII`, then N `(child block, separator key block)` pairs, then one final child `u32`. Therefore N keys partition N+1 children.
- Implemented recursive traversal with depth limit, cycle/shared-node detection, block bounds checks, separator resolution, final-child validation and descriptor path-count validation.
- Parsed the Apple oracle completely: `APPLE_MULTILEVEL_PASS 5001 5000 5001 A00000 A04999`.
- Unit suite now has 38 passing tests, including a synthetic internal-node fixture and cycle rejection.

### iOS AppIcon oracle
- Compiled a modern universal 1024×1024 AppIcon for `iphoneos`, target 15.0.
- actool emitted `Assets.car`, `AppIcon60x60@2x.png`, `AppIcon76x76@2x~ipad.png`, and partial-info plist entries for phone/iPad.
- AppIcon key format adds scale(12), idiom(15), subtype(16), dimension2(9), identifier(17), element(1), and part(2).
- Idiom IDs observed: phone=1, pad=2. Image part=220; auxiliary MSIS part=218. Facet part=220.
- 1024 image CSI: ARGB layout 12; rendition starts MLEC mode 3, codec 4, CBCK, followed by an LZFSE `bvx2` stream. This differs from the existing deepmap2 codec and remains oracle-gated until CBCK semantics are independently reproduced.
- Partial plist includes `CFBundleIconName=AppIcon`, phone `AppIcon60x60`, and iPad `AppIcon60x60`/`AppIcon76x76`.

## 2026-07-13 — iOS idiom and dark-appearance writer

- Built an Xcode 26.5 oracle containing universal 1×/2×, iPhone, iPad, and dark variants.
- Observed iOS image KEYFORMAT `(appearance=7, localization=13, scale=12, idiom=15, subtype=16, identifier=17, element=1, part=2)`.
- Observed values: universal=0, phone=1, pad=2; any appearance=0, `UIAppearanceDark`=1.
- APPEARANCEKEYS is a variable-key tree mapping `UIAppearanceAny`→little-endian u16 0 and `UIAppearanceDark`→u16 1.
- Extended `AssetRendition` and `png_rendition` with checked idiom and appearance selectors. The writer dynamically emits the iOS key format and APPEARANCEKEYS registry.
- Apple `assetutil` recognized the independent output's `Appearances` registry, universal/phone/pad idioms, dark rendition, and all payloads as deepmap2.
- Unit suite: 39 tests OK.

## 2026-07-13 — CBCK reverse engineering and independent AppIcon writer

### Oracle structure
Xcode 26.5's 1024×1024 opaque RGB AppIcon produced MLEC mode 3 / codec 4. The payload is:

```text
"MLEC" + u32(mode=3) + u32(codec=4) + u32(chunkCount)
repeat chunkCount:
    "KCBC"                 # reversed FourCC CBCK
    u32 reserved0 = 0
    u32 reserved1 = 0
    u32 rowCount
    u32 compressedLength
    independent LZFSE stream (bvx2 ... bvx$)
```

The oracle had four streams at offsets 36, 1031, 2026 and 3021. Row counts were 341, 341, 341 and 1; each full chunk decompresses to `1024 * 341 * 4 = 1,396,736` premultiplied BGRA bytes. Total reconstructed bytes are 4,194,304. Source RGB `20 60 a0` reconstructed as BGRA `a0 60 20 ff`.

### Implementation
- Added bounds-checked PNG → premultiplied BGRA conversion.
- Added chunked CBCK writer with independent optional-`lzfse` streams and an inferred Xcode chunk cap of `0x155555` raw bytes.
- Added MLEC mode 3 / codec 4 envelope.
- Added modern iOS AppIcon builder with phone/pad part-220 CBCK renditions, part-218 MSIS auxiliary renditions, dimension2 keys, and facet part 220.
- Added a 9-attribute AppIcon KEYFORMAT including `kCRThemeDimension2Name`.

### Verification
- 40 unit tests pass with LZFSE enabled.
- Local 1024 fixture: four chunks `[341,341,341,1]`, reconstructed 4,194,304 bytes, exact BGRA first pixel `a06020ff`.
- Apple Xcode 26.5 `assetutil` accepted the independently generated CAR and reported both phone and pad renditions as `Compression: lzfse`, `Encoding: ARGB`, 1024×1024, plus both MSIS records.
- An iOS 26.2 Simulator consumer test app was built and signed, but CoreSimulator boot stalled in this runner; no Simulator consumer pass is claimed for this milestone.

## 2026-07-13 — CBCK parser and iOS Simulator consumer validation

- Added a standalone bounds-checked `parse_cbck` reader with MLEC mode/codec checks, chunk-count limits, KCBC magic checks, row and compressed-length validation, trailing-byte rejection, and independent LZFSE decompression.
- Parsed the Apple AppIcon oracle into 4 chunks `[341,341,341,1]` and reconstructed all 4,194,304 BGRA bytes.
- Added `cbck_png_rendition` for ordinary part-181 image assets, allowing CBCK itself to be tested separately from AppIcon's special lookup semantics.
- Built, signed, installed and launched an arm64 UIKit app in the iOS 26.2 iPhone 17 Pro Simulator. `UIImage imageNamed:@"CBCKImage"` loaded the independent 1024×1024 CBCK CAR and wrote: `CBCK_SIM_PASS 1024 1024`.
- `UIImage imageNamed:@"AppIcon"` returned nil for both the Apple oracle and independent AppIcon CAR, confirming that AppIcon is not a valid ordinary named-image consumer test. The ordinary CBCK rendition is the positive decoder test.
- Test suite: 43 tests OK.

## 2026-07-13 — Integrated AppIcon CLI and high-contrast appearance

### AppIcon CLI
- `actool-linux ... --app-icon AppIcon --output-partial-info-plist ...` now consumes a modern single-source AppIcon set and emits all of: `Assets.car`, `AppIcon60x60@2x.png`, `AppIcon76x76@2x~ipad.png`, and the partial plist.
- Added deterministic pure-Python RGBA PNG resizing/encoding for 120×120 and 152×152 compatibility sidecars.
- Partial plist now includes `CFBundleIconName`, phone `AppIcon60x60`, and iPad `AppIcon60x60`/`AppIcon76x76` arrays.
- Apple verification: `sips` reported exact 120×120 and 152×152 dimensions; `plutil` accepted all icon dictionaries; `assetutil` accepted the CAR's phone/pad 1024×1024 ARGB/LZFSE and MSIS records.

### High contrast
- Xcode oracle maps `UIAppearanceHighContrastAny` to appearance ID 2 and uses a registry containing Any=0 and HighContrastAny=2.
- Generalized APPEARANCEKEYS allocation for arbitrary enabled Any/Dark/HighContrast records.
- `png_rendition(..., appearance="high-contrast")` emits ID 2.
- Apple assetutil recognized the independent registry and rendition as `UIAppearanceHighContrastAny`.
- Unit suite: 45 tests OK.

## 2026-07-13 — Legacy palette capability audit

The Xcode macOS AssetRuntime CoreUI binary was inspected only through observable `strings` output; no binary or private implementation is redistributed. Xcode 26.3 and current Xcode 26.5 both retain all of the following evidence:

```text
palette-img
allowsPaletteImageCompression
setAllowsPaletteImageCompression:
_allowsPaletteImageCompression
allowsDeepmap2ImageCompression
setAllowsDeepmap2ImageCompression:
CUIUncompressDeepmap2ImageData
CBCK
lzfse
kCoreThemeCompressionTypeLossless/Lossy/None/GPUOptimized...
```

Conclusion: current CoreUI still contains legacy `palette-img` recognition and a palette-compression enable/disable capability, so legacy consumer compatibility has not been completely removed. However, 24 controlled indexed-PNG actool builds across Xcode 16.0/16.4/26.3 all selected deepmap2, and the current `actool --help` exposes no palette toggle. Thus the legacy encoder path is retained but not proven reachable through the public actool CLI. Writer implementation remains oracle-gated until an actual palette-img CSI fixture is obtained.

Added `tools/coreui_capabilities.py`, which records binary path, size, SHA-256, matched observable capability strings, and explicit legacy evidence as reproducible JSON without copying framework contents.

## 2026-07-13 — Multi-level B+ tree writer

Implemented deterministic arbitrary-depth BOM B+ tree emission using reserved/stable block IDs. Verified layout details against the 5,000-facet Apple oracle:

- leaf: header, N value/key pairs, reserved u32, inline keys, padding;
- internal: header with N separators, N `(child,max-key)` pairs, final N+1 child u32, inline separator keys (no reserved u32), padding;
- each separator is the maximum key of its left child;
- forward/backward leaf links are emitted;
- upper levels are recursively grouped when necessary.

Large catalogs now switch to true multi-level RENDITIONS and FACETKEYS trees. BITMAPKEYS retains a large leaf because its numeric internal-key semantics differ. A 140-facet/140-rendition independently generated CAR had non-leaf roots for both main trees. Xcode 26.5 `assetutil` returned RC=0, all 140 names, and zero CoreUI size warnings. Unit suite: 46 tests OK.

## 2026-07-13 — Numeric BITMAPKEYS and localization writer

### Numeric BITMAPKEYS
Apple's 5,000-facet oracle showed numeric internal nodes use 63 `(child,numeric-separator)` pairs, a final child u32, no inline separator bytes, and fixed 1024-byte nodes. Leaves contain `(value block,numeric key)` pairs and links. Implemented this separate numeric path. A 140-facet CAR now has internal roots for RENDITIONS, FACETKEYS and BITMAPKEYS; Xcode 26.5 assetutil returned RC=0, all 140 names and zero warnings.

### Localization
Located a real LOCALIZATIONKEYS oracle in the macOS SFSymbols CoreGlyphs CAR. It is a variable-length tree mapping BCP-47-like tags (`ar`, `ja`, `zh-Hans`, `zh-Hant`, etc.) to little-endian u16 IDs. Added localization names to AssetRendition, deterministic collision-checked IDs, LOCALIZATIONKEYS emission for small and large catalogs, and `png_rendition(..., localization="ja")`. Apple assetutil recognized the independent registry and displayed localized `ja` and `ar` rendition names. Test suite: 47 tests OK.

## 2026-07-13 — SVG preserved vector and automatic fallbacks

Xcode 26.5 oracle established SVG vector CSI: part 42, pixel format `SVG `, layout 9, flags 4, RAWD payload; fallback part 181 renditions use deepmap2, flags 276, scales 1/2/3 and intrinsic raster sizes. Implemented validated SVG preservation, optional CairoSVG rasterization, automatic 1x/2x/3x deepmap fallbacks, direct API and catalog compiler integration. Apple assetutil recognized the independent part-42 rendition as Vector and all fallback dimensions/compression. AppKit main-bundle consumer loaded it: `SVG_APPKIT_PASS 10 20 50600`. Added optional `svg` and `all` dependencies. 48 tests OK.

## 2026-07-13 — Launch image CLI

Xcode 26.5 oracle showed legacy launch-image catalogs do not produce Assets.car for the tested iPhone 7.0 portrait 2x entry; they emit `Launch-700@2x.png` as an external sidecar. Added `--launch-image`, set discovery/diagnostics, minimum-system-version/scale/idiom filename mapping, and exact source preservation. Apple and Linux outputs had identical SHA-256 `1abf95e1...c32eddf`; `cmp` returned `LAUNCH_BYTE_PASS`. iPad `~ipad` naming and 1x/2x/3x suffix rules are implemented. 49 tests OK.

## 2026-07-13 — Cross-platform idioms and thinning selector

- Oracle observation: Xcode 26.5 watchOS ordinary image keys use idiom numeric ID 5 and include deployment-target key variants.
- Implemented checked CoreUI idiom mapping: universal=0, phone=1, pad=2, tv=3, car=4, watch=5, marketing=6, mac=7, vision=8.
- Implemented `ThinningOptions` / `thin_renditions` with idiom, scale, appearance, and localization selection, retaining universal/Any/unlocalized fallbacks by default.
- Added deterministic EXTENDED_METADATA thinning-argument emission.
- Linux test result: 52 tests, OK.
- Apple Xcode 26.5 `assetutil -I` result for independently written nine-idiom CAR: exit 0; labels recognized as `universal`, `phone`, `pad`, `tv`, `car`, `watch`, `marketing`, `mac`, and `vision`.
- Focused remote tests: 3 tests, OK. Full bare-system remote suite had expected optional-dependency failures because that Python lacks lzfse/cairosvg; these are environment failures, not regressions.

## 2026-07-13 — Symbol vector CAR writer

- Parsed the 153 MiB macOS CoreGlyphs `Assets.car`: 8,303 facets and 174,290 renditions.
- Observed symbol vectors use part 59, pixel format `SVG `, CSI layout 1017, flags 4, glyph-weight/glyph-size key attributes, and TLVs 1018/1019. Packed raster fallbacks use GA8 layouts 1003/1004.
- Added the complete 16-field symbol KEYFORMAT and symbol fields to the rendition intermediate representation.
- Added `symbol_rendition` / `build_symbol_car`, layout-1017 CSI, neutral bounded metrics, symbol-info TLV, and `.symbolset` `symbols` discovery/compiler integration.
- Apple Xcode 26.5 `assetutil -I` accepts the independent CAR and reports `AssetType: Vector Glyph` for `Glyph`.
- Local suite: 53 tests, OK; focused remote symbol test: OK.

## 2026-07-13 — Packed atlas writer and INLK metadata

- Parsed CoreGlyphs layout-1003 linked records and layout-1004 `ZZZZPackedAsset` pages.
- Reverse engineered TLV 1010: `KLNI`, version, x/y/width/height, reserved u16, `(attribute,value)` u16 tokens, zero terminator. Oracle bytes round-trip exactly.
- Implemented bounds-checked parser/writer, deterministic shelf packing, RGBA page composition, empty linked CSI records, and shared deepmap atlas page generation.
- Apple Xcode 26.5 `assetutil -I` accepts the independent output: `One`/`Two` are `Image`; the shared page is `PackedImage` at 8x4 pixels.
- Suite: 55 tests OK; focused remote atlas tests: 2 OK.

## 2026-07-13 — Multi-weight symbols and platform AppIcons

- Added SF Symbols template expansion for nine weights (`Ultralight`..`Black`) and S/M/L sizes. Groups such as `Regular-M` and `Bold-L` become distinct part-59 layout-1017 Vector Glyph renditions.
- Added platform AppIcon idiom selection: iOS phone+pad, tvOS tv, watchOS watch, macOS mac, visionOS vision, including simulator aliases.
- Apple Xcode 26.5 `assetutil` accepted all independently generated CARs. tv/watch/mac/vision each report `Icon Image` with `lzfse` plus `MultiSized Image` under the correct idiom. A two-weight template reports two `Vector Glyph` renditions.
- Local suite: 57 tests OK.

## 2026-07-13 — Layered icons, watch complication keys, sidecar manifests

- Added layer-key renditions and `build_layered_icon_car` for tvOS and visionOS; Xcode 26.5 assetutil reports two Image records with idiom tv/vision and Layer 1/2.
- Added watch complication subtype renditions; assetutil reports watch idiom with Subtype 1/2.
- Added compatibility sidecar manifests: 13 iOS/iPad PNGs, 9 watchOS PNGs, and 10 macOS PNGs. tvOS/visionOS remain layered in CAR and are intentionally not flattened.
- Local suite: 62 tests OK.

## 2026-07-13 — Fast-path runtime inventory and CLI contracts

- Added `tools/simulator_runtime_matrix.py`: inventories every runtime and optionally creates/boots/cleans one compatible device per runtime, persisting partial JSON after every attempt.
- Current Xcode 26.5 host inventory: 12 available runtimes — iOS 26.2/26.4.1/26.5, tvOS 26.2/26.4/26.5, watchOS 26.2/26.4/26.5, visionOS 26.2/26.4.1/26.5.
- Full boot pass was deferred after Simulator shutdown exceeded 30 seconds, per user request to postpone slow work. The inventory result is verified; display-consumer claims were not upgraded.
- Added CLI parsing and writer integration for target-device, device model/OS filters, product type, development region, PNG compression, and on-demand-resource switches. Single target-device selection is connected to deterministic thinning and records arguments in EXTENDED_METADATA.
- Suite: 64 tests OK.
