# 🧬 DeepWiki Module Specification: Quality Metrics & Ergonomics Safety Barriers (`actool::safety`)

Comprehensive architectural and algorithmic breakdown for all **5** modules in the `safety` domain layer.

--- 

## 📦 Module `actool::safety::autosafe`
- **Source File**: `actool/src/safety/autosafe.rs`
- **Lines of Code**: 307 LOC

### Overview
Ultra-High Precision Auto Safe Compress Pipeline

### Structs & Binary Types
#### `struct PrecisionSafetyReport`
```rust
pub struct PrecisionSafetyReport {
    pub is_lossless: bool,
    pub detected_domain: ImageDomain,
    pub alpha_type: AlphaCharacteristic,
    pub unique_color_count: usize,
    pub is_monochrome: bool,
    pub psnr_db: f64,
    pub delta_e: f64,
    pub ssim: f64,
    pub edge_preservation: f32,
    pub applied_strategy: String,
}
```

### Enums & Classification Types
#### `enum SafetyLevel`
```rust
pub enum SafetyLevel {
    StrictLossless,
    // Zero bit-level modification allowed (100% bit-exact)
    PerceptualSafe,
    // Quality-gated: PSNR > 42dB,
    ΔE < 1.5,
    SSIM > 0.98,
    Edge > 0.98
    CustomShaderSafe,
    // Preserves exact RGB in alpha=0 regions for Metal/OpenGL shaders
    AutoDomainDetect,
    // Intelligently infers domain (Normal maps,
    PBR,
    Glyphs,
    Noise,
    Photos),
}
```

#### `enum ImageDomain`
```rust
pub enum ImageDomain {
    NormalMap,
    // Tangent-space normal map (requires exact vectors)
    GlyphTextLine,
    // Sharp text,
    glyphs,
    line art (high spatial frequency)
    GrayscaleUI,
    // R=G=B monochrome (convertible to GA8 losslessly)
    PBRMaterial,
    // Metallic/Roughness/Occlusion textures
    Photographic,
    // Smooth gradients,
    complex continuous spectrum
    NoisyCameraGrain,
    // High frequency random noise
    BinaryPlaceholder,
    // Empty or tiny placeholders,
}
```

#### `enum AlphaCharacteristic`
```rust
pub enum AlphaCharacteristic {
    Opaque,
    // 100% Alpha = 255
    BinaryMask,
    // Alpha is strictly 0 or 255 (1-bit mask)
    GradualSmooth,
    // Fractional translucent alpha gradient
    DirtyAlpha,
    // Non-zero RGB where alpha = 0,
}
```

### Public Methods & API
- **`pub fn analyze_alpha_characteristic(bgra: &[u8]) -> AlphaCharacteristic`**
- **`pub fn detect_image_domain(bgra: &[u8], width: u32, height: u32) -> ImageDomain`**
- **`pub fn auto_safe_compress(bgra: &[u8], width: u32, height: u32, asset_kind: &str, safety_level: SafetyLevel,) -> (Vec<u8>, PrecisionSafetyReport)`**
- **`pub fn get_precision_report_json(report: &PrecisionSafetyReport) -> serde_json::Value`**

---

## 📦 Module `actool::safety::ciede2000`
- **Source File**: `actool/src/safety/ciede2000.rs`
- **Lines of Code**: 112 LOC

### Overview
Implements the full CIEDE2000 (ΔE00) Color Difference Formula according to ISO/CIE 11664-6:2014.
CIEDE2000 models human visual perception (HVS) with extreme precision, correcting for
lightness, chroma, hue, and blue-region non-linearities.
/// Threshold: ΔE00 <= 1.0 is the strict Just Noticeable Difference (JND) limit for 100% of human observers.

### Public Methods & API
- **`pub fn compute_ciede2000(lab1: (f64, f64, f64), lab2: (f64, f64, f64)) -> f64`**
- **`pub fn compute_image_ciede2000(orig_rgb: &[u8], comp_rgb: &[u8]) -> f64`**

---

## 📦 Module `actool::safety::ergonomics`
- **Source File**: `actool/src/safety/ergonomics.rs`
- **Lines of Code**: 73 LOC

### Overview
Human Ergonomics Ergonomic Safety Standard:
- ΔE00 <= 1.0 (CIEDE2000 JND threshold: 100% human observer imperceptibility)
- PSNR >= 45.0 dB (virtually mathematical lossless)
- SSIM >= 0.99 (structural integrity)
- Edge Preservation >= 0.99 (sharp font/text/UI edges)

### Structs & Binary Types
#### `struct ErgonomicHumanVisionReport`
```rust
pub struct ErgonomicHumanVisionReport {
    pub is_imperceptible_to_all_humans: bool,
    pub delta_e_00: f64,
    pub psnr_db: f64,
    pub ssim: f64,
    pub edge_preservation: f32,
    pub jnd_status: String,
}
```

### Public Methods & API
- **`pub fn evaluate_human_visual_ergonomics(orig_bgra: &[u8], comp_bgra: &[u8], width: usize, height: usize,) -> ErgonomicHumanVisionReport`**
- **`pub fn get_ergonomics_json(report: &ErgonomicHumanVisionReport) -> serde_json::Value`**

---

## 📦 Module `actool::safety::psychoacoustics`
- **Source File**: `actool/src/safety/psychoacoustics.rs`
- **Lines of Code**: 15 LOC

### Overview
Human Auditory Ergonomics (Psychoacoustics):
Minimum SNR >= 80.0 dB guarantees that audio noise floor remains below the threshold of
human perception in quiet listening conditions across all age groups.

### Public Methods & API
- **`pub fn evaluate_human_auditory_safety(original_pcm16: &[i16], processed_pcm16: &[i16],) -> (bool, f64)`**

---

## 📦 Module `actool::safety::quality_metrics`
- **Source File**: `actool/src/safety/quality_metrics.rs`
- **Lines of Code**: 177 LOC

### Public Methods & API
- **`pub fn compute_psnr(orig: &[u8], comp: &[u8]) -> f64`**
- **`pub fn rgb_to_lab(r_u8: u8, g_u8: u8, b_u8: u8) -> (f64, f64, f64)`**
- **`pub fn compute_delta_e(orig_rgb: &[u8], comp_rgb: &[u8]) -> f64`**
- **`pub fn compute_ssim(orig: &[u8], comp: &[u8]) -> f64`**
- **`pub fn sobel(bgra: &[u8], width: usize, height: usize) -> (Vec<f32>, Vec<f32>)`**
- **`pub fn compute_edge_preservation(orig: &[u8], comp: &[u8], width: usize, height: usize) -> f32`**
- **`pub fn evaluate_quality(orig: &[u8], comp: &[u8]) -> (f64, f64, f64)`**
- **`pub fn is_quality_acceptable(orig: &[u8], comp: &[u8], min_psnr: f64) -> bool`**

---

