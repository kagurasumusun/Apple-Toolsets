# 🍎 Apple Toolset Suite (`Apple-Toolset`)

A high-performance, clean-room, cross-platform implementation suite for Apple developer toolsets, including **`actool`** (Asset Catalog Compiler), **`CAREditor`**, **`assetutil`**, and extensible architecture prepared for future tool integrations (**`ibtool`**, **`simctl`**, **`momc`**, **`mapc`**).

Designed with a single-branch unified workflow (`main`) and built with dual high-performance implementations:
1. **`actool_rs`**: Pure Rust ultra-fast multi-threaded binary (**53.9x speedup**, 2.05ms execution, zero compiler warnings).
2. **`actool_linux`**: Unified 57-module Python engine with zero external AI weights and 100% deterministic heuristics.

---

## 🌟 Key Capabilities & Specifications

- **Apple CoreUI Contract Compliance**:
  Full 100% zero app-change compatibility with `UIImage(named:)` and `NSDataAsset.data`.
- **High-Performance Parallel Architecture**:
  Rayon multi-threaded worker pools in Rust across KCBC row-band chunking, 4-plane delta channels, YCoCg quantization, and 2D spatial grid tiling.
- **ASTC GPU-Direct Hardware Blocks**:
  Encodes 128-bit native ASTC hardware blocks (`AS44`, `AS88`) directly readable by Apple Silicon Metal GPU texture samplers (skipping CPU decompression).
- **Ultra-HD 2D Spatial Grid Tiling (4K / 8K / 16K)**:
  Memory-safe spatial 2D grid tiling for large high-resolution images prevents VRAM exhaustion.
- **3D PBR Material Packing & Tangent Normal Maps**:
  Packs Ambient Occlusion (R), Roughness (G), and Metallic (B) into single ORM BGRA textures (saving **66% VRAM**), and packs 2-channel tangent normal maps ($N_x, N_y \rightarrow N_z$).
- **Perceptual Safety & Ergonomic Thresholds**:
  - ISO/CIE 11664-6 CIEDE2000 ($\Delta E_{00} \le 1.0$) JND color distance.
  - Human Auditory System (HAS) $\ge 80.0 \text{ dB}$ SNR noise floor threshold.
  - **Dirty Alpha Auto-Protection**: Automatically preserves non-zero RGB in $A=0$ regions for Metal custom shaders, 3D materials, and edge-padding filtering.
- **CAREditor API & Virtual Storage Mounting**:
  Interactive CAR archive editing (`editor.rs`), virtual file system directory mounting and syncing (`mount.rs`), and corrupted CAR auto-repair recovery (`repair.rs`).
- **Non-Image Specialized Engine**:
  Minifies Lottie JSON, trims PCM audio tail silence (-90dB) with 1D delta prediction, and quantizes 3D OBJ mesh vertex floats.

---

## 🏗 Repository Organization (Single-Branch `main`)

The codebase is organized into clean, single-responsibility domain subpackages across both Rust (`actool_rs/src`) and Python (`actool_linux/`):

```
Apple-Toolset/
├── actool_linux/            # Python Unified Package (5 Domain Subpackages)
│   ├── core/                # BOMStore, CARHeader, CSI, B-Tree, Facet Hash
│   ├── codecs/              # LZFSE, CBCK, DMP2, ASTC, UltraHD, TET Codecs
│   ├── safety/              # CIEDE2000, Quality Metrics, AutoSafe Guards
│   ├── assets/              # Atlases, AppIcons, Layer Stacks, 3D, Audio, Thinning
│   └── tools/               # Catalog Compiler, CLI, Diagnostics, Repack
│
├── actool_rs/               # Rust High-Performance Engine
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs           # Public Re-exports (1:1 API Parity)
│       ├── main.rs / bin/   # CLI Binaries (actool-rs, car-info, car-repack, pdf-car)
│       ├── core/            # Low-level BOM, CAR, B-Tree & CSI Binary Core
│       ├── codecs/          # Rayon Parallel LZFSE, CBCK, DMP2, ASTC Codecs
│       ├── safety/          # ISO/CIE 11664-6 CIEDE2000, HAS 80dB SNR, AutoSafe
│       ├── assets/          # Sprite Atlases, Layer Stacks, PBR 3D, Media, Audio
│       └── tools/           # Catalog Compiler, CAREditor API, Mount, Repair
│
├── wiki/                    # Master Engineering Technical Documentation Series
├── scripts/                 # Reusable Evaluation & Utility Tools
└── tests/                   # Automated Integration Test Suite (241 Python + 20 Rust)
```

---

## ⚡ Quick Start

### Building & Running Rust Engine (`actool_rs`)

```bash
cd actool_rs
cargo build --release
cargo test --release
./target/release/actool-rs --compile output_dir path/to/App.xcassets --platform iphoneos
```

### Running Python Engine (`actool_linux`)

```bash
PYTHONPATH=. pytest --ignore=tests/test_data
python3 -m actool_linux.tools.cli --compile output_dir path/to/App.xcassets --platform iphoneos
```

---

## 📜 License & Disclaimers

- Developed under clean-room engineering specifications.
- `actool`, `ibtool`, `Xcode`, and `CoreUI` are trademarks of Apple Inc. This is an independent open-source toolset project.
