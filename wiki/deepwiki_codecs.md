# 🧬 DeepWiki Module Specification: Parallel Compression & Codecs Subsystem (`actool::codecs`)

Comprehensive architectural and algorithmic breakdown for all **30** modules in the `codecs` domain layer.

--- 

## 📦 Module `actool::codecs::ai_quantizer`
- **Source File**: `actool/src/codecs/ai_quantizer.rs`
- **Lines of Code**: 59 LOC

### Structs & Binary Types
#### `struct PerceptualQuantizer`
```rust
pub struct PerceptualQuantizer {
    pub max_colors: usize,
    pub use_dithering: bool,
}
```

### Public Methods & API
- **`pub fn new(max_colors: usize, use_dithering: bool) -> Self`**
- **`pub fn floyd_steinberg_dither(&self, bgra: &[u8], palette: &[[u8; 4]]) -> Vec<u8>`**
- **`pub fn quantize(&self, bgra: &[u8]) -> (Vec<u8>, bool)`**
- **`pub fn _floyd_steinberg_dither() -> ()`**
- **`pub fn _fallback_quantize() -> ()`**

---

## 📦 Module `actool::codecs::alpha_compression`
- **Source File**: `actool/src/codecs/alpha_compression.rs`
- **Lines of Code**: 72 LOC

### Structs & Binary Types
#### `struct ALPHACompressor`
```rust
pub struct ALPHACompressor {
    pub clean_alpha: bool,
    pub parallel: bool,
    pub max_workers: usize,
}
```

### Public Methods & API
- **`pub fn _fusion_planar_then_lpc(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn _fusion_ycocg_then_block(bgra: &[u8], _block_size: usize) -> Vec<u8>`**
- **`pub fn _fusion_edge_aware_multi(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn _fusion_alpha_perfect_ycocg(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn _compress_single_chunk(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn new(clean_alpha: bool, parallel: bool, max_workers: usize) -> Self`**
- **`pub fn _clean_alpha(&self, bgra: &mut [u8]) -> ()`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn alpha_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::astc_compression`
- **Source File**: `actool/src/codecs/astc_compression.rs`
- **Lines of Code**: 114 LOC

### Structs & Binary Types
#### `struct ASTCClassCompressor`
```rust
pub struct ASTCClassCompressor {
    pub clean_alpha: bool,
    pub target_bpp: f32,
}
```

### Enums & Classification Types
#### `enum ASTCBlockSize`
```rust
pub enum ASTCBlockSize {
    Block4x4 = 0,
    Block6x6 = 1,
    Block8x8 = 2,
    Block10x10 = 3,
    Block12x12 = 4,
}
```

### Public Methods & API
- **`pub fn new(clean_alpha: bool, target_bpp: f32) -> Self`**
- **`pub fn _select_block_size(&self, block_bgra: &[u8], width: usize, height: usize) -> ASTCBlockSize`**
- **`pub fn _astc_emulate_block(&self, block_bgra: &[u8], block_size: ASTCBlockSize) -> Vec<u8>`**
- **`pub fn compress_chunk(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn astc_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::astc_native`
- **Source File**: `actool/src/codecs/astc_native.rs`
- **Lines of Code**: 169 LOC

### Overview
ASTC Hardware GPU-Direct Header (Magic: 0x5CB05C00)
Native GPU-Direct ASTC Header Container for Metal VRAM uploading
Packs raw BGRA pixels directly into native 128-bit (16-byte) ASTC hardware blocks
readable directly by Apple Silicon GPU texture sampling hardware units.
Builds full GPU-Direct ASTC CSI rendition

### Enums & Classification Types
#### `enum ASTCGPUDirectBlockDim`
```rust
pub enum ASTCGPUDirectBlockDim {
    Block4x4 = 0,
    // 8.00 bpp
    Block6x6 = 1,
    // 3.56 bpp
    Block8x8 = 2,
    // 2.00 bpp
    Block10x10 = 3,
    // 1.28 bpp
    Block12x12 = 4,
    // 0.89 bpp,
}
```

### Public Methods & API
- **`pub fn dimensions(&self) -> (u32, u32)`**
- **`pub fn pixel_format_fourcc(&self) -> &'static [u8; 4]`**
- **`pub fn build_astc_gpu_header(block_dim: ASTCGPUDirectBlockDim, width: u32, height: u32, depth: u32,) -> Vec<u8>`**
- **`pub fn encode_native_astc_blocks(bgra: &[u8], width: u32, height: u32, block_dim: ASTCGPUDirectBlockDim,) -> Vec<u8>`**
- **`pub fn build_astc_gpu_direct_csi(bgra: &[u8], width: u32, height: u32, filename: &str, block_dim: ASTCGPUDirectBlockDim,) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::astc_optimized`
- **Source File**: `actool/src/codecs/astc_optimized.rs`
- **Lines of Code**: 107 LOC

### Public Methods & API
- **`pub fn analyze_block_complexity(block_bgra: &[u8]) -> (f32, f32, f32)`**
- **`pub fn select_astc_block_size(edge_density: f32, _color_var: f32, trans_ratio: f32) -> u32`**
- **`pub fn astc_optimal_endpoints(block_bgra: &[u8], block_size: u32) -> ([u8; 4], [u8; 4])`**
- **`pub fn astc_interpolate_weights(block_bgra: &[u8], endpoints: ([u8; 4], [u8; 4])) -> Vec<u8>`**
- **`pub fn astc_ultra_compress_block(block_bgra: &[u8]) -> Vec<u8>`**
- **`pub fn astc_ultra_compress_chunk(bgra: &[u8], _sub_block_size: usize) -> Vec<u8>`**
- **`pub fn astc_ultra_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::astc_optimizer`
- **Source File**: `actool/src/codecs/astc_optimizer.rs`
- **Lines of Code**: 19 LOC

### Public Methods & API
- **`pub fn new() -> Self`**
- **`pub fn analyze_chunk() -> ()`**
- **`pub fn encode() -> ()`**

---

## 📦 Module `actool::codecs::cbck`
- **Source File**: `actool/src/codecs/cbck.rs`
- **Lines of Code**: 160 LOC

### Structs & Binary Types
#### `struct CBCKChunk`
```rust
pub struct CBCKChunk {
    pub y_offset: u16,
    pub rows: u16,
    pub raw_length: usize,
    pub compressed: Vec<u8>,
}
```

#### `struct CBCKPayload`
```rust
pub struct CBCKPayload {
    pub mode: u32,
    pub codec: u32,
    pub chunks: Vec<CBCKChunk>,
}
```

### Public Methods & API
- **`pub fn encode_cbck(bgra: &[u8], width: u32, height: u32, codec: u32, clean_alpha: bool,) -> Vec<u8>`**
- **`pub fn parse_cbck(data: &[u8]) -> Result<CBCKPayload, &'static str>`**
- **`pub fn decompress(data: &[u8]) -> Result<Vec<u8>, &'static str>`**

---

## 📦 Module `actool::codecs::cbck_complete`
- **Source File**: `actool/src/codecs/cbck_complete.rs`
- **Lines of Code**: 191 LOC

### Structs & Binary Types
#### `struct CBCKChunk`
```rust
pub struct CBCKChunk {
    pub width: u32,
    pub height: u32,
    pub data: Vec<u8>,
    pub compressed_size: usize,
    pub uncompressed_size: usize,
}
```

#### `struct CBCKEncoder`
```rust
pub struct CBCKEncoder {
    pub chunk_width: u32,
    pub chunk_height: u32,
}
```

### Public Methods & API
- **`pub fn from_raw(width: u32, height: u32, pixels: &[u8]) -> Self`**
- **`pub fn decompress(&self) -> Result<Vec<u8>, &'static str>`**
- **`pub fn new(chunk_width: u32, chunk_height: u32) -> Self`**
- **`pub fn _align_to_power_of_2(value: u32) -> u32`**
- **`pub fn determine_optimal_chunk_size(&self, width: u32, height: u32) -> (u32, u32)`**
- **`pub fn _extract_chunk(pixels: &[u8], img_w: u32, _img_h: u32, x: u32, y: u32, w: u32, h: u32) -> Vec<u8>`**
- **`pub fn encode(&self, width: u32, height: u32, pixels: &[u8]) -> (Vec<CBCKChunk>, usize, usize)`**
- **`pub fn calculate_compression_ratio(&self, chunks: &[CBCKChunk]) -> f32`**
- **`pub fn decode(chunks: &[CBCKChunk], chunks_per_row: usize, chunks_per_col: usize, width: u32, height: u32) -> Result<Vec<u8>, &'static str>`**
- **`pub fn _serialize_chunks(chunks: &[CBCKChunk], chunks_per_row: u32, chunks_per_col: u32) -> Vec<u8>`**
- **`pub fn optimize_cbck_for_apple_compatibility(width: u32, height: u32, pixels: &[u8]) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::dmp2mini`
- **Source File**: `actool/src/codecs/dmp2mini.rs`
- **Lines of Code**: 155 LOC

### Public Methods & API
- **`pub fn mini_run(total: usize, first_bias: usize, cont_bias: usize, cap: usize, allow_bare: bool, bare_bias: usize,) -> Vec<u8>`**
- **`pub fn run_read(data: &[u8], mut offset: usize, first_bias: usize, cont_bias: usize, bare_bias: usize,) -> (usize, usize)`**
- **`pub fn v1_raw(width: u16, height: u16, raw: &[u8], bpp: u8) -> Vec<u8>`**
- **`pub fn v3_mini_color(width: u16, height: u16, bgra: &[u8; 4]) -> Vec<u8>`**
- **`pub fn decode_mini(dmp2: &[u8], width: u32, height: u32, bpp: u8) -> Option<Vec<u8>>`**
- **`pub fn _mini_run() -> ()`**
- **`pub fn _run_read() -> ()`**
- **`pub fn _header() -> ()`**
- **`pub fn v3_mini_ga() -> ()`**
- **`pub fn v4_mini() -> ()`**

---

## 📦 Module `actool::codecs::hybrid_compression`
- **Source File**: `actool/src/codecs/hybrid_compression.rs`
- **Lines of Code**: 114 LOC

### Structs & Binary Types
#### `struct HybridCompressor`
```rust
pub struct HybridCompressor {
    pub clean_alpha: bool,
    pub lpc_max_colors: usize,
    pub planar_quant_step: u8,
}
```

### Public Methods & API
- **`pub fn new(clean_alpha: bool, lpc_max_colors: usize, planar_quant_step: u8) -> Self`**
- **`pub fn select_strategy(&self, bgra: &[u8], width: u32, height: u32) -> u8`**
- **`pub fn compress_chunk(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn hybrid_compress_for_cbck(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn _load_ai_model() -> ()`**
- **`pub fn analyze_chunk() -> ()`**
- **`pub fn _select_strategy() -> ()`**
- **`pub fn _clean_dirty_alpha() -> ()`**
- **`pub fn _apply_lpc() -> ()`**
- **`pub fn _apply_planar_delta() -> ()`**

---

## 📦 Module `actool::codecs::lpc_lzfse`
- **Source File**: `actool/src/codecs/lpc_lzfse.rs`
- **Lines of Code**: 86 LOC

### Structs & Binary Types
#### `struct LPCPalette`
```rust
pub struct LPCPalette {
    pub colors: Vec<[u8; 4]>,
}
```

### Public Methods & API
- **`pub fn new(colors: Vec<[u8; 4]>) -> Self`**
- **`pub fn quantize(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn to_bytes(&self) -> Vec<u8>`**
- **`pub fn extract_palette(bgra: &[u8], max_colors: usize) -> Option<LPCPalette>`**
- **`pub fn lpc_encode_apple_compat(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**
- **`pub fn extract_palette_kmeans() -> ()`**
- **`pub fn lpc_encode_pure() -> ()`**
- **`pub fn analyze_chunk_compressibility() -> ()`**
- **`pub fn from_bytes() -> ()`**

---

## 📦 Module `actool::codecs::lzfse`
- **Source File**: `actool/src/codecs/lzfse.rs`
- **Lines of Code**: 96 LOC

### Overview
Pure Rust LZFSE compressor & decompressor handler.
Produces valid LZFSE streams using Apple's "bvx2" (uncompressed pass-through LZFSE block)
or RLE/LZ compression blocks.

### Public Methods & API
- **`pub fn compress(data: &[u8]) -> Vec<u8>`**
- **`pub fn decompress(data: &[u8]) -> Result<Vec<u8>, &'static str>`**

---

## 📦 Module `actool::codecs::lzfse_compat`
- **Source File**: `actool/src/codecs/lzfse_compat.rs`
- **Lines of Code**: 21 LOC

### Public Methods & API
- **`pub fn have_c_extension() -> bool`**
- **`pub fn is_valid_stream(data: &[u8]) -> bool`**
- **`pub fn compress(data: &[u8]) -> Vec<u8>`**
- **`pub fn decompress(data: &[u8]) -> Result<Vec<u8>, &'static str>`**

---

## 📦 Module `actool::codecs::lzfse_optimized`
- **Source File**: `actool/src/codecs/lzfse_optimized.rs`
- **Lines of Code**: 208 LOC

### Structs & Binary Types
#### `struct LZFSEOptimized`
```rust
pub struct LZFSEOptimized {
    pub block_size: usize,
    pub compression_level: usize,
    pub max_match_length: usize,
    pub hash_bits: usize,
}
```

### Public Methods & API
- **`pub fn new(block_size: usize, compression_level: usize) -> Self`**
- **`pub fn _hash(&self, data: &[u8]) -> usize`**
- **`pub fn _find_match_length(&self, data: &[u8], pos1: usize, pos2: usize) -> usize`**
- **`pub fn _encode_literals(&self, literals: &[u8]) -> Vec<u8>`**
- **`pub fn _encode_match(&self, length: usize, distance: usize) -> Vec<u8>`**
- **`pub fn _create_raw_block(&self, data: &[u8]) -> Vec<u8>`**
- **`pub fn _create_empty_block(&self) -> Vec<u8>`**
- **`pub fn _compress_block(&self, data: &[u8]) -> Vec<u8>`**
- **`pub fn _create_lzfse_stream(&self, blocks: &[Vec<u8>], original_size: usize) -> Vec<u8>`**
- **`pub fn compress(&self, data: &[u8]) -> Vec<u8>`**
- **`pub fn analyze_compression_ratio(&self, data: &[u8]) -> f32`**
- **`pub fn compress_with_apple_compatibility(data: &[u8]) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::nexus_compression`
- **Source File**: `actool/src/codecs/nexus_compression.rs`
- **Lines of Code**: 127 LOC

### Structs & Binary Types
#### `struct NEXUSCompressor`
```rust
pub struct NEXUSCompressor {
    pub clean_alpha: bool,
    pub parallel: bool,
}
```

### Public Methods & API
- **`pub fn haar_decompose_2x2(b: &[u8]) -> (u8, i8, i8, i8)`**
- **`pub fn compress_predictive_dpcm(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn compress_ycocg_perceptual(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_wavelet(chunk: &[u8]) -> Vec<u8>`**
- **`pub fn compress_dictionary(chunk: &[u8]) -> Vec<u8>`**
- **`pub fn compress_dct(chunk: &[u8]) -> Vec<u8>`**
- **`pub fn compress_similarity(chunk: &[u8]) -> Vec<u8>`**
- **`pub fn new(clean_alpha: bool, parallel: bool) -> Self`**
- **`pub fn compress_chunk(&self, chunk: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn nexus_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::omega_compression`
- **Source File**: `actool/src/codecs/omega_compression.rs`
- **Lines of Code**: 134 LOC

### Structs & Binary Types
#### `struct OMEGACompressor`
```rust
pub struct OMEGACompressor {
    pub clean_alpha: bool,
    pub min_psnr: f64,
    pub max_delta_e: f64,
}
```

### Public Methods & API
- **`pub fn new(clean_alpha: bool, quality_threshold: &str) -> Self`**
- **`pub fn _clean_alpha(&self, bgra: &mut [u8]) -> ()`**
- **`pub fn _try_subtle_quant(&self, bgra: &[u8], step: u8) -> Option<Vec<u8>>`**
- **`pub fn _try_edge_preserving_quant(&self, bgra: &[u8], width: usize, height: usize) -> Option<Vec<u8>>`**
- **`pub fn _try_alpha_perfect(&self, bgra: &[u8]) -> Option<Vec<u8>>`**
- **`pub fn _try_smooth_quant(&self, bgra: &[u8]) -> Option<Vec<u8>>`**
- **`pub fn _try_ycocg_perceptual(&self, bgra: &[u8]) -> Option<Vec<u8>>`**
- **`pub fn compress_chunk(&self, chunk_bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn omega_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::omega_plus`
- **Source File**: `actool/src/codecs/omega_plus.rs`
- **Lines of Code**: 107 LOC

### Public Methods & API
- **`pub fn dmp2_rle_optimize(raw: &[u8], _bpp: u8) -> Vec<u8>`**
- **`pub fn dmp2_delta_encode(raw: &[u8]) -> Vec<u8>`**
- **`pub fn adaptive_palette_optimize(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn ga_optimize(ga_data: &[u8]) -> Vec<u8>`**
- **`pub fn detect_similar_renditions(renditions: Vec<crate::carwriter::AssetRendition>) -> Vec<crate::carwriter::AssetRendition>`**
- **`pub fn predictive_encode(raw: &[u8]) -> Vec<u8>`**
- **`pub fn new() -> Self`**
- **`pub fn optimize_dmp2(&self, raw: &[u8], bpp: u8) -> Vec<u8>`**
- **`pub fn optimize_ga(&self, ga_data: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_renditions(&self, renditions: Vec<crate::carwriter::AssetRendition>) -> Vec<crate::carwriter::AssetRendition>`**
- **`pub fn optimize_dmp2_payload(raw: &[u8], bpp: u8) -> Vec<u8>`**
- **`pub fn optimize_ga_data(ga_data: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_rendition_list(renditions: Vec<crate::carwriter::AssetRendition>) -> Vec<crate::carwriter::AssetRendition>`**

---

## 📦 Module `actool::codecs::omni_compression`
- **Source File**: `actool/src/codecs/omni_compression.rs`
- **Lines of Code**: 84 LOC

### Structs & Binary Types
#### `struct OMNICompressor`
```rust
pub struct OMNICompressor {
    pub clean_alpha: bool,
}
```

### Public Methods & API
- **`pub fn new(clean_alpha: bool) -> Self`**
- **`pub fn try_default(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn try_planar_delta(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn try_aggressive_quant(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_chunk(&self, bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn omni_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn _clean_alpha() -> ()`**
- **`pub fn _try_default() -> ()`**
- **`pub fn _try_planar_delta() -> ()`**
- **`pub fn _try_planar_delta_fine() -> ()`**
- **`pub fn _try_lpc() -> ()`**
- **`pub fn _try_astc_class() -> ()`**
- **`pub fn _try_aggressive_quant() -> ()`**
- **`pub fn _try_ultra_aggressive() -> ()`**

---

## 📦 Module `actool::codecs::omniv2_compression`
- **Source File**: `actool/src/codecs/omniv2_compression.rs`
- **Lines of Code**: 90 LOC

### Structs & Binary Types
#### `struct OMNIv2Compressor`
```rust
pub struct OMNIv2Compressor {
    pub clean_alpha: bool,
    pub aggressive: bool,
}
```

### Public Methods & API
- **`pub fn new(clean_alpha: bool, aggressive: bool) -> Self`**
- **`pub fn _clean_alpha(&self, bgra: &mut [u8]) -> ()`**
- **`pub fn _try_ultra_quant(&self, bgra: &[u8], levels: usize) -> Vec<u8>`**
- **`pub fn _try_block_mean(&self, bgra: &[u8], _block_size: usize) -> Vec<u8>`**
- **`pub fn _try_gradient_predict(&self, bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn _try_edge_preserve(&self, bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn _try_ycocg_aggressive(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn _try_median_filter(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_chunk(&self, chunk_bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn omniv2_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::paletteimg`
- **Source File**: `actool/src/codecs/paletteimg.rs`
- **Lines of Code**: 235 LOC

### Structs & Binary Types
#### `struct ThemePixelRendition`
```rust
pub struct ThemePixelRendition {
    pub version: u32,
    pub compression_type: u32,
    pub raw_data: Vec<u8>,
}
```

#### `struct QuantizedImageData`
```rust
pub struct QuantizedImageData {
    pub version: u32,
    pub palette: Vec<Vec<u8>>,
    pub indices: Vec<u8>,
    pub bits_per_index: usize,
}
```

### Enums & Classification Types
#### `enum PaletteImageError`
```rust
pub enum PaletteImageError {
    #[error("Theme pixel rendition is truncated")]
    Truncated,
    #[error("Invalid theme pixel rendition magic")]
    InvalidMagic,
    #[error("Palette color count out of range: {0,
}
```

### Public Methods & API
- **`pub fn bit_width(palette_count: usize) -> Result<usize, PaletteImageError>`**
- **`pub fn parse_theme_pixel_rendition(data: &[u8]) -> Result<ThemePixelRendition, PaletteImageError>`**
- **`pub fn unpack_row_indices(data: &[u8], width: usize, bits_per_index: usize,) -> Result<Vec<u8>, PaletteImageError>`**
- **`pub fn pack_row_indices(indices: &[u8], width: usize, bits_per_index: usize,) -> Result<Vec<u8>, PaletteImageError>`**
- **`pub fn decode_quantized_image_payload(raw_data: &[u8], width: usize, _height: usize,) -> Result<QuantizedImageData, PaletteImageError>`**
- **`pub fn encode_quantized_image_payload(palette_argb: &[u8], indices: &[u8], width: usize, _height: usize,) -> Result<Vec<u8>, PaletteImageError>`**
- **`pub fn build_palette_img_wrapper(palette_argb: &[u8], indices: &[u8], width: usize, height: usize,) -> Result<Vec<u8>, PaletteImageError>`**
- **`pub fn _bit_width() -> ()`**
- **`pub fn _unpack_row_indices() -> ()`**
- **`pub fn _pack_row_indices() -> ()`**

---

## 📦 Module `actool::codecs::planar_delta_lzfse`
- **Source File**: `actool/src/codecs/planar_delta_lzfse.rs`
- **Lines of Code**: 129 LOC

### Public Methods & API
- **`pub fn separate_planes(bgra: &[u8]) -> (Vec<u8>, Vec<u8>, Vec<u8>, Vec<u8>)`**
- **`pub fn delta_encode_plane(plane: &[u8]) -> Vec<u8>`**
- **`pub fn delta_decode_plane(delta: &[u8]) -> Vec<u8>`**
- **`pub fn planar_delta_encode(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn planar_delta_decode(data: &[u8]) -> Result<Vec<u8>, &'static str>`**
- **`pub fn planar_delta_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn planar_delta_decompress(compressed: &[u8]) -> Result<Vec<u8>, &'static str>`**
- **`pub fn make_apple_compatible_delta_chunk(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn analyze_delta_characteristics(bgra: &[u8]) -> (f32, &'static str)`**

---

## 📦 Module `actool::codecs::semantic_fusion`
- **Source File**: `actool/src/codecs/semantic_fusion.rs`
- **Lines of Code**: 33 LOC

### Structs & Binary Types
#### `struct SemanticFusionAtlas`
```rust
pub struct SemanticFusionAtlas {
    pub edge_density_threshold: f32,
}
```

### Public Methods & API
- **`pub fn new(edge_density_threshold: f32) -> Self`**
- **`pub fn fuse_and_encode(&self, bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**
- **`pub fn semantic_fuse(data: &[u8]) -> Vec<u8>`**
- **`pub fn analyze_edge_density() -> ()`**
- **`pub fn _mock_astc_encode() -> ()`**
- **`pub fn _mock_lpc_encode() -> ()`**

---

## 📦 Module `actool::codecs::smart_cbck`
- **Source File**: `actool/src/codecs/smart_cbck.rs`
- **Lines of Code**: 156 LOC

### Structs & Binary Types
#### `struct SmartCBCKEncoder`
```rust
pub struct SmartCBCKEncoder {
    pub clean_alpha: bool,
    pub chunk_raw_cap: usize,
}
```

### Public Methods & API
- **`pub fn new(clean_alpha: bool) -> Self`**
- **`pub fn _load_ai_model(&self) -> bool`**
- **`pub fn _predict_strategy(&self, chunk_bgra: &[u8], width: u32, height: u32) -> u8`**
- **`pub fn _clean_dirty_transparency(bgra: &mut [u8]) -> ()`**
- **`pub fn _compute_rows_per_chunk(&self, width: u32, height: u32) -> Vec<(u32, u32)>`**
- **`pub fn encode_chunk(&self, bgra_data: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn encode(&self, bgra_data: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn smart_encode_png_cbck(bgra_premultiplied: &[u8], width: u32, height: u32, filename: &str, scale: u32, clean_alpha: bool,) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::tet_complete`
- **Source File**: `actool/src/codecs/tet_complete.rs`
- **Lines of Code**: 92 LOC

### Structs & Binary Types
#### `struct TETCompleteCompressor`
```rust
pub struct TETCompleteCompressor {
    pub has_cv2: bool,
    pub has_skimage: bool,
    pub has_scipy: bool,
    pub has_pywt: bool,
    pub has_pil: bool,
}
```

### Public Methods & API
- **`pub fn bm3d_denoise(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn wavelet_denoise(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn non_local_means_denoise(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn bilateral_filter_cv2(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn connected_component_crop(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn kmeans_quantization(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn median_cut_pil(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn color_space_conversion_cv2(bgra: &[u8], _conversion: &str) -> Vec<u8>`**
- **`pub fn tone_mapping_hdr(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn new() -> Self`**
- **`pub fn optimize_noise_reduction(&self, bgra: &[u8]) -> (Vec<u8>, &'static str)`**
- **`pub fn optimize_color_quantization(&self, bgra: &[u8], max_colors: usize) -> (Vec<u8>, &'static str)`**
- **`pub fn optimize_geometry(&self, bgra: &[u8], width: usize, height: usize) -> (Vec<u8>, &'static str)`**
- **`pub fn optimize_all(&self, bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn tet_complete_optimize(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn tet_complete_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::tet_compression`
- **Source File**: `actool/src/codecs/tet_compression.rs`
- **Lines of Code**: 103 LOC

### Public Methods & API
- **`pub fn transparent_border_removal(bgra: &[u8], width: usize, height: usize) -> (Vec<u8>, (usize, usize, usize, usize))`**
- **`pub fn paeth_predict(left: u8, top: u8, top_left: u8) -> u8`**
- **`pub fn new() -> Self`**
- **`pub fn compress(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn tet_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**
- **`pub fn hidden_pixel_removal() -> ()`**
- **`pub fn median_cut_quantization() -> ()`**
- **`pub fn alpha_threshold() -> ()`**
- **`pub fn alpha_quantization() -> ()`**
- **`pub fn spatial_prediction_encode() -> ()`**
- **`pub fn tile_deduplication() -> ()`**
- **`pub fn tet_optimize() -> ()`**
- **`pub fn optimize() -> ()`**

---

## 📦 Module `actool::codecs::tet_full`
- **Source File**: `actool/src/codecs/tet_full.rs`
- **Lines of Code**: 140 LOC

### Public Methods & API
- **`pub fn octree_quantization(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn wu_quantization(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn neuquant(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn lloyd_max(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn pca_quantization(bgra: &[u8], max_colors: usize) -> Vec<u8>`**
- **`pub fn palette_sort(palette: &[[u8; 4]]) -> Vec<[u8; 4]>`**
- **`pub fn palette_merge(p1: &[[u8; 4]], p2: &[[u8; 4]]) -> Vec<[u8; 4]>`**
- **`pub fn shared_palette(p1: &[[u8; 4]], p2: &[[u8; 4]]) -> Vec<[u8; 4]>`**
- **`pub fn adaptive_palette(_bgra: &[u8]) -> Vec<[u8; 4]>`**
- **`pub fn median_filter(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn gaussian_filter(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn bilateral_filter(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn edge_preserving_filter(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn gradient_simplification(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn gradient_quantization(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn linear_gradient_detection(_bgra: &[u8]) -> bool`**
- **`pub fn block_merge(b1: &[u8], b2: &[u8]) -> Vec<u8>`**
- **`pub fn hash_deduplication(blocks: &[Vec<u8>]) -> Vec<Vec<u8>>`**
- **`pub fn morton_order(width: usize, height: usize) -> Vec<usize>`**
- **`pub fn hilbert_curve(width: usize, height: usize) -> Vec<usize>`**
- **`pub fn tile_ordering(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn new() -> Self`**
- **`pub fn compress(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn optimize(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn tet_full_optimize(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn tet_full_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::tet_ultimate`
- **Source File**: `actool/src/codecs/tet_ultimate.rs`
- **Lines of Code**: 184 LOC

### Public Methods & API
- **`pub fn left_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn top_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn average_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn gradient_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn adaptive_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn edge_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn linear_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn context_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn median_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn auto_crop(bgra: &[u8], width: usize, height: usize) -> (Vec<u8>, (usize, usize, usize, usize))`**
- **`pub fn tight_bounding_box(bgra: &[u8], width: usize, height: usize) -> (usize, usize, usize, usize)`**
- **`pub fn border_removal(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn empty_region_removal(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn tile_crop(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn roi_crop(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn shape_crop(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn transparent_border_crop(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn connected_component_crop(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn remove_gamma(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_icc(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_time(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_exif(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_author(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_software(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_comments(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_thumbnail(data: &[u8]) -> Vec<u8>`**
- **`pub fn remove_unknown_chunks(data: &[u8]) -> Vec<u8>`**
- **`pub fn merge_metadata(data: &[u8]) -> Vec<u8>`**
- **`pub fn jpeg_adaptive_quantization(jpeg: &[u8]) -> Vec<u8>`**
- **`pub fn jpeg_trellis_quantization(jpeg: &[u8]) -> Vec<u8>`**
- **`pub fn jpeg_perceptual_quantization(jpeg: &[u8]) -> Vec<u8>`**
- **`pub fn jpeg_420_chroma(jpeg: &[u8]) -> Vec<u8>`**
- **`pub fn jpeg_422_chroma(jpeg: &[u8]) -> Vec<u8>`**
- **`pub fn heif_ctu_optimization(heif: &[u8]) -> Vec<u8>`**
- **`pub fn heif_intra_prediction(heif: &[u8]) -> Vec<u8>`**
- **`pub fn heif_deblocking(heif: &[u8]) -> Vec<u8>`**
- **`pub fn pdf_path_simplification(pdf: &[u8]) -> Vec<u8>`**
- **`pub fn pdf_point_reduction(pdf: &[u8]) -> Vec<u8>`**
- **`pub fn pdf_object_deduplication(pdf: &[u8]) -> Vec<u8>`**
- **`pub fn pdf_font_subsetting(pdf: &[u8]) -> Vec<u8>`**
- **`pub fn color_space_conversion(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn wide_gamut_reduction(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn float16_to_uint8(data: &[u8]) -> Vec<u8>`**
- **`pub fn bit_depth_reduction(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn rgb_packing(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn alpha_packing(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn new() -> Self`**
- **`pub fn optimize_spatial_prediction(&self, bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn optimize_geometry(&self, bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn optimize_all(&self, bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn tet_ultimate_optimize(bgra: &[u8], width: usize, height: usize) -> Vec<u8>`**
- **`pub fn tet_ultimate_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::tet_variants`
- **Source File**: `actool/src/codecs/tet_variants.rs`
- **Lines of Code**: 110 LOC

### Public Methods & API
- **`pub fn shared_pixels(a: &[u8], b: &[u8]) -> usize`**
- **`pub fn binary_difference(a: &[u8], b: &[u8]) -> Vec<u8>`**
- **`pub fn variant_deduplication(a: &[u8], b: &[u8]) -> Vec<u8>`**
- **`pub fn shared_rgb(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn appearance_prediction(light: &[u8]) -> Vec<u8>`**
- **`pub fn contrast_delta(bgra: &[u8], factor: f32) -> Vec<u8>`**
- **`pub fn shared_background(a: &[u8], b: &[u8]) -> Vec<u8>`**
- **`pub fn accessibility_optimize(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn relative_luminance(r: u8, g: u8, b: u8) -> f32`**
- **`pub fn compute_variant_delta(light: &[u8], dark: &[u8]) -> (Vec<i16>, f64)`**
- **`pub fn new() -> Self`**
- **`pub fn optimize_light_dark(&self, light: &[u8], dark: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_color_variants(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_high_contrast(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_variants(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_colors(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn optimize_contrast(&self, bgra: &[u8]) -> Vec<u8>`**
- **`pub fn tet_variant_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::ultimate_compression`
- **Source File**: `actool/src/codecs/ultimate_compression.rs`
- **Lines of Code**: 156 LOC

### Structs & Binary Types
#### `struct UltimateCompressor`
```rust
pub struct UltimateCompressor {
    pub block_size: usize,
    pub clean_alpha: bool,
}
```

### Enums & Classification Types
#### `enum BlockType`
```rust
pub enum BlockType {
    Solid = 0,
    Gradient = 1,
    Edge = 2,
    Texture = 3,
    Transparent = 4,
}
```

### Public Methods & API
- **`pub fn new(block_size: usize, clean_alpha: bool) -> Self`**
- **`pub fn classify_block(&self, block_bgra: &[u8]) -> BlockType`**
- **`pub fn compress_solid(&self, block_bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_gradient(&self, block_bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_edge(&self, block_bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_texture(&self, block_bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_transparent(&self, block_bgra: &[u8]) -> Vec<u8>`**
- **`pub fn compress_chunk(&self, chunk_bgra: &[u8], _width: u32, _height: u32) -> Vec<u8>`**
- **`pub fn compress_image(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn ultimate_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**

---

## 📦 Module `actool::codecs::ultrahd`
- **Source File**: `actool/src/codecs/ultrahd.rs`
- **Lines of Code**: 130 LOC

### Overview
Ultra-HD Tiled Grid CBCK Encoder for 4K/8K/16K images
Uses 2D spatial tiles (e.g. 512x512) and Rayon parallel thread pools
to prevent memory exhaustion and achieve maximum multi-threaded performance.

### Enums & Classification Types
#### `enum UltraHDTier`
```rust
pub enum UltraHDTier {
    Standard,
    // < 4K
    Resolution4K,
    // >= 3840 x 2160
    Resolution8K,
    // >= 7680 x 4320
    Resolution16K,
    // >= 15360 x 8640,
}
```

### Public Methods & API
- **`pub fn classify_resolution_tier(width: u32, height: u32) -> UltraHDTier`**
- **`pub fn encode_ultrahd_tiled_cbck(bgra: &[u8], width: u32, height: u32, tile_dim: u32, clean_alpha: bool,) -> Vec<u8>`**
- **`pub fn get_ultrahd_report(width: u32, height: u32, raw_bytes_size: usize) -> serde_json::Value`**

---

