# actool-linux Engineering Handoff

Last updated: 2026-07-13 (Etc/GMT-9)

## Mission and clean-room boundary

Build a Linux-capable clean-room replacement for Apple `actool` and CoreUI CAR generation. Generated CARs must be accepted by Apple `assetutil` and, where tested, AppKit/UIKit/Simulator consumers. Observe public command behavior and generated data; do not copy or redistribute Apple binaries/private framework source. Keep readers bounds-checked. Never claim 100% compatibility without evidence.

Maintain reproducible evidence in `ENGINEERING_LOG.md`: commands, inputs, outputs, hashes, accepted/rejected hypotheses, and verification boundaries. Distinguish implemented, Apple `assetutil` verified, AppKit verified, UIKit Simulator verified, and experimental.

## User constraints

- Japanese responses; implementation and repeated validation are preferred over planning.
- Mac commands/tools/Simulators are approved substitutes for non-Mac physical devices.
- Never execute `exit`, `logout`, Ctrl-D, or terminate the shared tmux/Upterm shell. Detach only.
- Slow runtime boot/screenshot matrices are currently deferred at the user's request; prioritize short equivalent checks.
- Deliver a ZIP after every milestone.
- Legacy palette-img may use the public references listed by the user, but Apple code/binaries must not be copied.

## Current workspace and artifact

Local source tree: `/home/user/actool-linux`

Latest ZIP: `/home/user/actool-linux-source.zip`

The local Git repository has an old baseline and the current source is represented as working-tree changes/untracked files. Do not use local `git archive`; create ZIP from the filesystem excluding `.git`, caches, and build directories.

Current test command:

```bash
cd /home/user/actool-linux
PYTHONPATH=src python -m unittest discover -s tests
```

Latest result: 64 tests, OK.

Capability report:

```bash
PYTHONPATH=src python -m actool_linux.cli --capabilities
```

## Current remote Mac

Upterm session: `jNGXJkmYQMCMVK0wv6sZ`

SSH:

```bash
chmod 600 /home/user/.ssh/arena_upterm_ed25519
ssh -i /home/user/.ssh/arena_upterm_ed25519 \
  jNGXJkmYQMCMVK0wv6sZ@uptermd.upterm.dev
```

Use `/home/user/run_upterm_command.py SESSION COMMAND WAIT_SECONDS` for short commands. Use `run_upterm_interrupt.py` only for a genuinely stuck foreground process.

SCP transfers work even though SCP may return status `-1` after transferring. Verify the remote file explicitly:

```bash
scp -i /home/user/.ssh/arena_upterm_ed25519 \
  /home/user/actool-linux-source.zip \
  jNGXJkmYQMCMVK0wv6sZ@uptermd.upterm.dev:/Users/runner/actool-linux-source.zip
```

Remote host observed:

```text
macOS 26.4
Xcode 26.5
Build 17F42
assetutil DumpToolVersion 974.1
```

The repository at `/Users/runner/work/mac/mac` on this new runner is only the upstream workflow repository (`a069646`) and does not contain actool-linux. The uploaded source was extracted at:

```text
/Users/runner/actool-linux-current/actool-linux
```

Bare remote Python lacks optional `lzfse` and `cairosvg`; CBCK/SVG fallback tests fail there for dependency reasons. Use local Linux results or transfer already-generated CARs for Apple `assetutil` checks.

## Verified Xcode generations

`apple-consumer-matrix.json` contains 100/100 passing `assetutil` consumer rows across five SDK families (`macosx`, `iphoneos`, `appletvos`, `watchos`, `xros`) and these Xcode releases:

```text
Xcode 16.0
Xcode 16.1
Xcode 16.2
Xcode 16.3
Xcode 16.4
Xcode 26.0.1
Xcode 26.1.1
Xcode 26.2
Xcode 26.3
```

This is reader acceptance of a mixed independently generated CAR, not complete actool behavioral equivalence.

Additional focused Apple validation was performed with Xcode 26.5 for CBCK, AppIcons, vector glyphs, packed atlases, idioms, localization, appearance, SVG, layers, and complication subtype keys.

`xcode-matrix.json` is an actool build matrix with 100 rows: 60 pass, 38 build-failed, 2 build-timeout. Do not misreport this as 100/100 pass. `actool-contract.json` contains 20 Xcode installations/aliases and captured CLI contracts.

## Simulator inventory

Current new host has 12 available runtimes:

```text
iOS 26.2, 26.4.1, 26.5
tvOS 26.2, 26.4, 26.5
watchOS 26.2, 26.4, 26.5
visionOS 26.2, 26.4.1, 26.5
```

Inventory is saved in `simulator-runtime-inventory.json`.

Tool: `tools/simulator_runtime_matrix.py`. It supports inventory and optional bounded boot mode, incrementally saving JSON. A full boot pass was attempted but Simulator shutdown exceeded the 30-second cleanup timeout. The user then requested that time-consuming checks be deferred. Do not restart the all-runtime boot pass unless asked.

Runtime consumer actually verified previously:

```text
iOS 26.2 Simulator, iPhone 17 Pro, CBCK/UIKit consumer PASS
```

## Implemented and verification status

### BOM/CAR core — implemented and Apple verified

- Big-endian BOMStore parser/writer.
- CARHEADER, EXTENDED_METADATA, KEYFORMAT.
- Bounds-checked CSI/TLV parser.
- FACETKEYS, RENDITIONS, BITMAPKEYS.
- Arbitrary-depth B+ trees with internal separators, numeric BITMAPKEYS, and leaf links.
- 140-facet independent all-multilevel CAR accepted by Apple.
- 5,000-facet Apple oracle parsed.

### Images/data/colors — implemented and Apple verified

- DATA / NSDataAsset.
- JPEG, HEIF/HEIC.
- sRGB and Display P3 colors.
- PNG deepmap2 GA8, RGB, RGBA, indexed 1/2/4/8-bit, GA16, Adam7.
- Premultiplied BGRA and palette LZFSE.
- PDF preserved vector + deepmap fallbacks.
- SVG direct vector + automatic fallbacks.
- AppKit checks for JPEG/HEIF/colors/data/PDF/SVG.

### CBCK — implemented and Apple/UIKit verified

Grammar:

```text
MLEC
u32 mode=3
u32 codec=4
u32 chunkCount
repeat: KCBC, reserved0, reserved1, rowCount, compressedLength, LZFSE stream
```

Modern AppIcon part 220 and MSIS part 218 implemented. Apple reports ARGB/LZFSE. iOS 26.2 UIKit consumer passed. Complete all-Xcode adoption thresholds remain incomplete.

### AppIcons and platform idioms — implemented and assetutil verified

CoreUI idioms:

```text
universal=0 phone=1 pad=2 tv=3 car=4 watch=5 marketing=6 mac=7 vision=8
```

Modern CBCK/MSIS icon records support iOS/iPadOS, tvOS, watchOS, macOS, and visionOS plus simulator aliases. Xcode 26.5 assetutil reported the correct idiom, `Icon Image`, `MultiSized Image`, and LZFSE.

Compatibility sidecar manifests:

- 13 iOS/iPad PNGs.
- 9 watchOS PNGs.
- 10 macOS PNGs.
- tvOS/visionOS are intentionally not flattened.

### Symbols — implemented and assetutil verified

- `.symbolset` `symbols` discovery.
- Part 59, pixel format SVG, layout 1017, flags 4.
- 16-field glyph KEYFORMAT.
- TLV 1018 metrics and 1019 symbol information.
- SF template expansion for nine weights and S/M/L.
- Xcode 26.5 reports `Vector Glyph`.
- Advanced symbol effects/motion/color and complete raster atlas fallback remain partial.

### Packed atlas — implemented and assetutil verified

- TLV 1010 INLK/KLNI parser/writer.
- Exact 54-byte oracle round trip.
- Deterministic shelf packing and RGBA page composition.
- Layout 1003 empty linked records.
- Layout 1004 shared `ZZZZPackedAsset` deepmap page.
- Xcode 26.5 reports the shared page as `PackedImage` and linked entries as images.
- Xcode's exact packing heuristic/page splitting is not reproduced.

### Layered images / complications — implemented key representation, partially Apple verified

- tvOS/visionOS ordered `kCRThemeLayerName` renditions.
- visionOS depth value in `kCRThemeDimension2Name`.
- Watch family IDs in subtype and role IDs in dimension2.
- Xcode 26.5 verified basic tv/vision layer 1/2 and watch subtype 1/2 recognition.
- Latest explicit depth and semantic family/role mapping is locally tested; do not call it proprietary compositor/registry-equivalent without a new Apple oracle.

### Thinning — implemented, policy partial

- Idiom, scale, appearance, localization selection.
- Universal/Any/unlocalized fallback retention.
- EXTENDED_METADATA thinning arguments.
- CLI single target-device integration.
- Exact device-model policy remains partial.

### CLI — partial

Accepted/integrated options include compile, platform, deployment target, app icon, launch image, partial plist, diagnostics toggles, target device, model/OS filters, product type, development region, PNG compression, and ODR switch.

Complete Apple plist output, every option combination, stdout/stderr order, and byte-identical diagnostics are not done.

## Key format discoveries

Generic base:

```text
appearance, localization, element, part, size, identifier, layer, scale
```

Modern iOS variants:

```text
appearance, localization, scale, idiom, subtype, identifier, element, part
```

AppIcon adds dimension2. Symbol format:

```text
appearance, localization, element, part, direction, identifier,
dimension1, dimension2, state, presentationState, scale,
previousState, previousValue, deploymentTarget, glyphWeight, glyphSize
```

## Unfinished work — do not claim complete

- All 12 Simulator build/install/launch/materialization matrix.
- tvOS/visionOS/watchOS equivalent runtime apps.
- SpringBoard, tvOS Home, watch Home/complication, vision Home, and macOS Dock screenshot comparisons.
- All macOS generation AppKit matrix.
- Exact tvOS Image Stack compositor aggregate record.
- Apple-internal watch family/role registry mapping.
- Apple-internal vision depth/parallax compositor metadata.
- Full CLI option cross-product and byte-identical diagnostics.
- Complete CBCK adoption thresholds across every Xcode.
- Legacy palette-img writer (fixture-gated).
- Exact Xcode atlas pack/page heuristic.
- Full AppIcon metadata and every platform's deployment side effects.

## Recommended short next steps

1. Run focused `assetutil -I` on CARs containing explicit vision depth and named watch family/role keys; compare raw rendition keys, not semantic labels assetutil does not expose.
2. Add a parser for tvOS Image Stack aggregate records from a valid Xcode oracle. The previous attempted catalog emitted no Assets.car because the nested schema was incomplete.
3. Expand `tools/actool_contract.py` with malformed JSON, duplicate slots, wrong dimensions, and unsupported option combinations, recording raw stdout/stderr SHA-256.
4. Build a CBCK threshold probe that uses `actool` only and dimensions around `0x155555 / rowBytes`; this is short and avoids Simulator boot.
5. For runtime work, test one representative runtime per platform first. Do not run all 12 serial boots until cleanup behavior is stable.
6. Regenerate local ZIP, test with `unzip -t`, compute SHA-256, and present it.

## Push limitation

Historical actool-linux commits on the previous runner were ahead of origin, but GitHub push failed with HTTP 403 because the Actions token lacks write permission. Required workflow permission:

```yaml
permissions:
  contents: write
```

The new runner's `/Users/runner/work/mac/mac` contains only the upstream workflow repository. The source ZIP is the authoritative transfer artifact for this session.
