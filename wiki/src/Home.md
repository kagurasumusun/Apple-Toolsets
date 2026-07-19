# Apple Toolsets (`Apple-Toolsets`) DeepWiki Architecture Suite

Welcome to the official **DeepWiki Codebase Documentation Suite** for `Apple-Toolsets` — a high-performance, 100% pure Rust Apple Developer Toolset compilation engine suite (`apple-toolsets`).

This DeepWiki provides an AST-extracted, 1:20 master technical reference covering binary layouts, CoreUI archive specifications, ASTC hardware blocks, ISO/CIE 11664-6 CIEDE2000 color distance formulas, Rayon parallelism models, and non-image asset optimizers.

---

## DeepWiki Codebase Architecture & Domain Deep Dives

- **[1. Core Binary & Storage Engine (`actool::core`)](deepwiki_core.md)**:
  BOMStore 32-byte header, Block Indexes, Variables Tables, 436-byte `CARHEADER`, 12-byte `b"tree"` B-Tree descriptors, Facet Hash16, MultiDB, and ZeroCode DB.
- **[2. Parallel Compression & Codecs Subsystem (`actool::codecs`)](deepwiki_codecs.md)**:
  Deepmap (`dmp2` v1/v2/v3/v4), DMP2 Mini ISA opcodes, MLEC Mode 3 Codec 4/11 CBCK (`KCBC` chunks), Ultra-HD 4K/8K/16K spatial 2D grid tiling, 128-bit ASTC GPU-Direct hardware blocks (`AS44`, `AS88`), and Planar Delta.
- **[3. Quality Metrics & Ergonomics Safety Barriers (`actool::safety`)](deepwiki_safety.md)**:
  ISO/CIE 11664-6 CIEDE2000 ($\Delta E_{00} \le 1.0$) JND color distance, 80dB HAS psychoacoustic noise floor thresholds, `AutoDomainDetect` 4-gate safety barriers, and **Dirty Alpha Protection** ($A=0$ non-zero RGB preservation for Metal custom shaders and filtering).
- **[4. Advanced Asset Types, Atlases & 3D Engine (`actool::assets`)](deepwiki_assets.md)**:
  Sprite Atlases, LINK renditions (Layout 1003), AppIcons, Layer Stacks, PBR 3D ORM texture packing (66% VRAM reduction), 2-channel tangent normal maps ($N_x, N_y \rightarrow N_z$), Media entropy classification, and Thinning.
- **[5. Compiler, CAREditor API & Management Tools (`actool::tools`)](deepwiki_tools.md)**:
  `actool-rs` CLI, `CAREditor` interactive CAR modification API, virtual directory mounting & syncing (`mount.rs`), corrupted CAR auto-repair engine (`repair.rs`), Lottie JSON float truncation, PCM audio tail silence trimming (-90dB), and 3D OBJ mesh vertex float quantization.

---

## 📚 Master Engineering Technical Series (1:20 Specifications)

1. **[01: CoreUI CAR File & BOMStore Architecture](6_algorithmic_research/01_CAR_AND_BOM_FORMAT.md)**
2. **[02: Image Compression, Deepmap & CBCK Anatomy](6_algorithmic_research/02_IMAGE_COMPRESSION_AND_CBCK.md)**
3. **[03: Beyond God-Mode: Ergonomics, Auto-Safe Protection & 3D PBR](6_algorithmic_research/03_BEYOND_GODMODE_ALGORITHMS.md)**
4. **[04: CLI Tools, CAREditor API, Virtual Mounting & Non-Image Engine](6_algorithmic_research/04_TOOLS_AND_CLI.md)**
5. **[05: Facet Hash16 Anatomy & The 100% Accuracy Lookup Table](6_algorithmic_research/05_FACET_HASH16_ANATOMY.md)**

---

## Developer API Index (AST Auto-Extracted)

- **[Pure Rust API Reference Matrix](7_developer_api_reference/INDEX.md)**

---

## 📊 Status & Audits

- **[Final Status Report](3_progress_and_status/FINAL_STATUS.md)**: 100% Pure Rust migration certification, 0 compiler warnings, 20/20 test pass verification, and clean single-branch `main` status.
- **[Engineering Log](1_architecture/ENGINEERING_LOG.md)**: Engineering audit, 53.9x Rust speedup benchmarks, and logic-by-logic bug hunt fixes.

---
*Maintained by kagurasumusun — July 2026.*
