# 🧬 DeepWiki Module Specification: Compiler, CAREditor API & Management Tools (`actool::tools`)

Comprehensive architectural and algorithmic breakdown for all **12** modules in the `tools` domain layer.

--- 

## 📦 Module `actool::tools::capabilities`
- **Source File**: `actool/src/tools/capabilities.rs`
- **Lines of Code**: 14 LOC

### Public Methods & API
- **`pub fn capability_report() -> Value`**

---

## 📦 Module `actool::tools::catalog`
- **Source File**: `actool/src/tools/catalog.rs`
- **Lines of Code**: 118 LOC

### Overview
Safely resolve relative file within base directory preventing directory traversal

### Structs & Binary Types
#### `struct ContentsJsonInfo`
```rust
pub struct ContentsJsonInfo {
    pub version: u32,
    pub author: Option<String>,
}
```

#### `struct ContentsJsonImageEntry`
```rust
pub struct ContentsJsonImageEntry {
    pub idiom: Option<String>,
    pub size: Option<String>,
    pub scale: Option<String>,
    pub filename: Option<String>,
    pub platform: Option<String>,
    pub role: Option<String>,
    pub subtype: Option<String>,
}
```

#### `struct ContentsJson`
```rust
pub struct ContentsJson {
    pub info: Option<ContentsJsonInfo>,
    pub images: Option<Vec<ContentsJsonImageEntry>>,
}
```

#### `struct Asset`
```rust
pub struct Asset {
    pub name: String,
    pub kind: String,
    pub directory: PathBuf,
    pub entries: Vec<ContentsJsonImageEntry>,
}
```

#### `struct Catalog`
```rust
pub struct Catalog {
    pub root: PathBuf,
    pub assets: Vec<Asset>,
}
```

### Public Methods & API
- **`pub fn safe_resolve_file(base_dir: &Path, relative: &str) -> Option<PathBuf>`**

---

## 📦 Module `actool::tools::cli`
- **Source File**: `actool/src/tools/cli.rs`
- **Lines of Code**: 116 LOC

### Public Methods & API
- **`pub fn main_cli() -> ()`**
- **`pub fn write_stdout_bytes() -> ()`**
- **`pub fn parser() -> ()`**

---

## 📦 Module `actool::tools::compiler`
- **Source File**: `actool/src/tools/compiler.rs`
- **Lines of Code**: 279 LOC

### Structs & Binary Types
#### `struct CompileOptions`
```rust
pub struct CompileOptions {
    pub inputs: Vec<PathBuf>,
    pub output_dir: PathBuf,
    pub platform: String,
    pub minimum_deployment_target: String,
    pub app_icon: Option<String>,
    pub optimize: Option<String>,
    pub export_dependency_info: Option<PathBuf>,
    pub output_format: String,
}
```

#### `struct CompileResult`
```rust
pub struct CompileResult {
    pub diagnostics: Vec<Diagnostic>,
    pub output_files: Vec<PathBuf>,
}
```

### Public Methods & API
- **`pub fn color_component(val: f32) -> u8`**
- **`pub fn layer_depth(asset: &Asset) -> usize`**
- **`pub fn appearance_for(entry_appearance: Option<&str>) -> u16`**
- **`pub fn partial_info(platform: &str, target: &str) -> Value`**
- **`pub fn resolve_image_stack_layers(asset: &Asset, assets: &[Asset]) -> Vec<PathBuf>`**
- **`pub fn compile_brand_assets(inputs: &[PathBuf], options: &CompileOptions,) -> Result<Vec<PathBuf>, String>`**
- **`pub fn compile_catalogs(options: CompileOptions) -> Result<CompileResult, String>`**

---

## 📦 Module `actool::tools::diagnostics`
- **Source File**: `actool/src/tools/diagnostics.rs`
- **Lines of Code**: 94 LOC

### Structs & Binary Types
#### `struct Diagnostic`
```rust
pub struct Diagnostic {
    pub level: DiagnosticLevel,
    pub message: String,
    pub path: Option<PathBuf>,
}
```

### Enums & Classification Types
#### `enum DiagnosticLevel`
```rust
pub enum DiagnosticLevel {
    Notice,
    Warning,
    Error,
}
```

### Public Methods & API
- **`pub fn format_xml_plist(diagnostics: &[Diagnostic], output_files: &[PathBuf]) -> String`**
- **`pub fn version_plist() -> ()`**
- **`pub fn unknown_argument_plist() -> ()`**
- **`pub fn result_plist() -> ()`**
- **`pub fn render_human_readable() -> ()`**

---

## 📦 Module `actool::tools::editor`
- **Source File**: `actool/src/tools/editor.rs`
- **Lines of Code**: 89 LOC

### Structs & Binary Types
#### `struct CAREditor`
```rust
pub struct CAREditor {
    pub platform: String,
    pub renditions: HashMap<String,
    AssetRendition>,
}
```

### Public Methods & API
- **`pub fn new(platform: &str) -> Self`**
- **`pub fn add_or_replace_image(&mut self, name: &str, bgra: &[u8], width: u32, height: u32) -> ()`**
- **`pub fn remove_asset(&mut self, name: &str) -> bool`**

---

## 📦 Module `actool::tools::legacy_coreui_features`
- **Source File**: `actool/src/tools/legacy_coreui_features.rs`
- **Lines of Code**: 131 LOC

### Structs & Binary Types
#### `struct LegacyCompatibilityMode`
```rust
pub struct LegacyCompatibilityMode {
    pub target_version: u32,
    pub target_platform: String,
}
```

### Public Methods & API
- **`pub fn max_image_size(version: u32) -> u32`**
- **`pub fn is_feature_supported(version: u32, feature: &str) -> bool`**
- **`pub fn supported_compressions(version: u32) -> Vec<&'static str>`**
- **`pub fn default_scale(platform: &str) -> u16`**
- **`pub fn max_atlas_size(platform: &str) -> u32`**
- **`pub fn new(target_version: u32, target_platform: &str) -> Self`**
- **`pub fn validate_image_size(&self, width: u32, height: u32) -> (bool, String)`**
- **`pub fn get_version_specific_key_format(version: u32) -> Vec<u16>`**
- **`pub fn create_legacy_compatible_car(version: u32, platform: &str) -> LegacyCompatibilityMode`**
- **`pub fn get_version_specific_header_format() -> ()`**
- **`pub fn get_features() -> ()`**
- **`pub fn get_max_image_size() -> ()`**
- **`pub fn get_supported_compressions() -> ()`**
- **`pub fn get_supported_scales() -> ()`**
- **`pub fn get_max_atlas_size() -> ()`**
- **`pub fn validate_compression() -> ()`**
- **`pub fn validate_facet_name() -> ()`**
- **`pub fn validate_scale() -> ()`**
- **`pub fn validate_all() -> ()`**
- **`pub fn get_recommended_compression() -> ()`**
- **`pub fn get_recommended_atlas_size() -> ()`**

---

## 📦 Module `actool::tools::model`
- **Source File**: `actool/src/tools/model.rs`
- **Lines of Code**: 41 LOC

### Structs & Binary Types
#### `struct Diagnostic`
```rust
pub struct Diagnostic {
    pub severity: String,
    pub message: String,
    pub path: Option<PathBuf>,
}
```

#### `struct Asset`
```rust
pub struct Asset {
    pub catalog: PathBuf,
    pub directory: PathBuf,
    pub kind: String,
    pub name: String,
    pub properties: HashMap<String,
    String>,
    pub entries: Vec<HashMap<String,
    String>>,
}
```

#### `struct Catalog`
```rust
pub struct Catalog {
    pub path: PathBuf,
    pub assets: Vec<Asset>,
    pub diagnostics: Vec<Diagnostic>,
}
```

### Public Methods & API
- **`pub fn render(&self) -> String`**
- **`pub fn load_catalog() -> ()`**

---

## 📦 Module `actool::tools::mount`
- **Source File**: `actool/src/tools/mount.rs`
- **Lines of Code**: 62 LOC

---

## 📦 Module `actool::tools::nonimage_optimizer`
- **Source File**: `actool/src/tools/nonimage_optimizer.rs`
- **Lines of Code**: 180 LOC

### Overview
1. JSON & Lottie Animation Optimization
Strips formatting whitespace, truncates float precision (e.g. keyframe points) to 4 decimal places,
and applies structural LZFSE compression.
2. PCM Audio Optimization & Silence Tail Trimming
Trims dead tail silence below -90dB, applies PCM sample delta prediction, and LZFSE compresses.
3. 3D Mesh Geometry Coordinates Quantization & Index Delta Encoding
Quantizes 32-bit float vertex positions (v x y z) into 16-bit fixed point and delta encodes face indices.
4. PDF Vector Path Point Simplification
Strips redundant PDF stream operators and compresses object streams.
5. Universal Non-Image Auto Optimizer Router

### Structs & Binary Types
#### `struct NonImageOptimizationResult`
```rust
pub struct NonImageOptimizationResult {
    pub original_bytes: usize,
    pub optimized_bytes: usize,
    pub savings_percent: f64,
    pub asset_category: &'static str,
    pub applied_technique: String,
    pub payload: Vec<u8>,
}
```

### Public Methods & API
- **`pub fn optimize_json_lottie(raw_json: &[u8]) -> NonImageOptimizationResult`**
- **`pub fn optimize_pcm_audio_advanced(pcm_bytes: &[u8]) -> NonImageOptimizationResult`**
- **`pub fn optimize_3d_mesh_geometry(mesh_data: &[u8]) -> NonImageOptimizationResult`**
- **`pub fn optimize_vector_pdf_advanced(pdf_bytes: &[u8]) -> NonImageOptimizationResult`**
- **`pub fn optimize_non_image_asset(filename: &str, data: &[u8],) -> NonImageOptimizationResult`**

---

## 📦 Module `actool::tools::repack`
- **Source File**: `actool/src/tools/repack.rs`
- **Lines of Code**: 29 LOC

### Public Methods & API
- **`pub fn main() -> ()`**

---

## 📦 Module `actool::tools::repair`
- **Source File**: `actool/src/tools/repair.rs`
- **Lines of Code**: 68 LOC

### Structs & Binary Types
#### `struct RepairReport`
```rust
pub struct RepairReport {
    pub recovered_blocks: usize,
    pub recovered_renditions: usize,
    pub magic_repaired: bool,
    pub status: String,
}
```

### Public Methods & API
- **`pub fn repair_corrupted_car(raw_data: &[u8]) -> Result<(Vec<u8>, RepairReport), String>`**

---

