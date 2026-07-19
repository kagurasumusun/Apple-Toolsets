# 🧬 DeepWiki Module Specification: Advanced Asset Types, Atlases & 3D Engine (`actool::assets`)

Comprehensive architectural and algorithmic breakdown for all **15** modules in the `assets` domain layer.

--- 

## 📦 Module `actool::assets::appicons`
- **Source File**: `actool/src/assets/appicons.rs`
- **Lines of Code**: 65 LOC

### Structs & Binary Types
#### `struct AppIconEntry`
```rust
pub struct AppIconEntry {
    pub idiom: Option<String>,
    pub size: Option<String>,
    pub scale: Option<String>,
    pub filename: Option<String>,
    pub platform: Option<String>,
}
```

### Public Methods & API
- **`pub fn app_icon_entry_rank(entry: &AppIconEntry, platform: &str) -> Option<(i32, u32, u32)>`**
- **`pub fn _canonical_platform() -> ()`**
- **`pub fn app_icon_sidecar_specs() -> ()`**

---

## 📦 Module `actool::assets::arresource`
- **Source File**: `actool/src/assets/arresource.rs`
- **Lines of Code**: 38 LOC

### Structs & Binary Types
#### `struct ARReferenceImageSpec`
```rust
pub struct ARReferenceImageSpec {
    pub name: String,
    pub physical_width_meters: f32,
    pub physical_height_meters: f32,
}
```

#### `struct ARResourceGroup`
```rust
pub struct ARResourceGroup {
    pub name: String,
    pub reference_images: Vec<ARReferenceImageSpec>,
}
```

### Public Methods & API
- **`pub fn new(name: &str) -> Self`**
- **`pub fn add_image(&mut self, image: ARReferenceImageSpec) -> ()`**
- **`pub fn serialize_ar_group(&self) -> String`**

---

## 📦 Module `actool::assets::atlas`
- **Source File**: `actool/src/assets/atlas.rs`
- **Lines of Code**: 155 LOC

### Structs & Binary Types
#### `struct AtlasKeyToken`
```rust
pub struct AtlasKeyToken {
    pub attribute: u16,
    pub value: u16,
}
```

#### `struct AtlasLink`
```rust
pub struct AtlasLink {
    pub x: u32,
    pub y: u32,
    pub width: u32,
    pub height: u32,
    pub tokens: Vec<AtlasKeyToken>,
    pub variant: String,
    pub header_u16: u16,
    pub header_u32: u32,
}
```

#### `struct AtlasNameList`
```rust
pub struct AtlasNameList {
    pub names: Vec<String>,
}
```

#### `struct AtlasTrim`
```rust
pub struct AtlasTrim {
    pub original_width: u32,
    pub original_height: u32,
    pub origin_x: u32,
    pub origin_y: u32,
    pub trimmed_width: u32,
    pub trimmed_height: u32,
}
```

### Public Methods & API
- **`pub fn parse_atlas_link(raw: &[u8]) -> Result<AtlasLink, &'static str>`**
- **`pub fn build_atlas_link(x: u32, y: u32, width: u32, height: u32, tokens: &[AtlasKeyToken]) -> Vec<u8>`**
- **`pub fn parse_atlas_name_list(raw: &[u8]) -> Result<AtlasNameList, &'static str>`**
- **`pub fn parse_atlas_trim(raw: &[u8]) -> Result<AtlasTrim, &'static str>`**
- **`pub fn _linked_csi() -> ()`**
- **`pub fn _atlas_name_list_tlv() -> ()`**
- **`pub fn _atlas_metadata_csi() -> ()`**
- **`pub fn _png_rgba() -> ()`**
- **`pub fn _alpha_bbox() -> ()`**
- **`pub fn _crop_rgba() -> ()`**
- **`pub fn _explicit_trim_tlv() -> ()`**
- **`pub fn packed_atlas_renditions() -> ()`**
- **`pub fn packed_watch_complication_renditions() -> ()`**
- **`pub fn build_packed_atlas_car() -> ()`**
- **`pub fn chunk() -> ()`**

---

## 📦 Module `actool::assets::atlas_geometry`
- **Source File**: `actool/src/assets/atlas_geometry.rs`
- **Lines of Code**: 131 LOC

### Public Methods & API
- **`pub fn improved_shelf_pack(rects: &[(u32, u32)], max_width: u32, max_height: u32,) -> (Vec<(u32, u32)>, u32, u32)`**
- **`pub fn apple_style_pack(rects: &[(u32, u32)], max_width: u32, _max_height: u32,) -> (Vec<(u32, u32)>, u32, u32)`**
- **`pub fn calculate_packing_efficiency(positions: &[(u32, u32)], rects: &[(u32, u32)], atlas_w: u32, atlas_h: u32) -> f32`**

---

## 📦 Module `actool::assets::audio`
- **Source File**: `actool/src/assets/audio.rs`
- **Lines of Code**: 156 LOC

### Overview
Quality-Gated Audio Optimization Engine
Ensures PCM audio is compressed safely without audio pops, SNR degradation (< 60dB SNR barrier), or THD distortion.

### Structs & Binary Types
#### `struct AudioQualityReport`
```rust
pub struct AudioQualityReport {
    pub is_lossless: bool,
    pub original_bytes: usize,
    pub compressed_bytes: usize,
    pub snr_db: f64,
    pub thd_percent: f64,
    pub applied_strategy: String,
}
```

### Enums & Classification Types
#### `enum AudioFormat`
```rust
pub enum AudioFormat {
    CompressedAAC,
    // m4a,
    aac (Pass-through to prevent generation loss)
    CompressedMP3,
    // mp3 (Pass-through)
    UncompressedPCM,
    // wav,
    caf,
    aiff (Quality-gated LPC/ADPCM/LZFSE compression)
    HapticPattern,
    // ahap json,
}
```

### Public Methods & API
- **`pub fn compute_signal_to_noise_ratio_db(signal_pcm16: &[i16], processed_pcm16: &[i16]) -> f64`**
- **`pub fn detect_audio_format(filename: &str, data: &[u8]) -> AudioFormat`**
- **`pub fn optimize_audio_payload(filename: &str, pcm_bytes: &[u8], _min_snr_db: f64,) -> (Vec<u8>, AudioQualityReport)`**
- **`pub fn get_audio_report_json(report: &AudioQualityReport) -> serde_json::Value`**

---

## 📦 Module `actool::assets::iconstack`
- **Source File**: `actool/src/assets/iconstack.rs`
- **Lines of Code**: 213 LOC

### Structs & Binary Types
#### `struct IconStackRootStyleEntry`
```rust
pub struct IconStackRootStyleEntry {
    pub kind: u32,
    pub value: f32,
    pub enabled: u8,
    pub reserved_hex: String,
}
```

#### `struct IconStackAuxEntry`
```rust
pub struct IconStackAuxEntry {
    pub u32_1: u32,
    pub f32_1: f32,
    pub u32_2: u32,
    pub f32_2: f32,
    pub u32_3: u32,
}
```

#### `struct IconStackGroupStyleReference`
```rust
pub struct IconStackGroupStyleReference {
    pub count: u32,
    pub kind: u32,
    pub name: String,
}
```

#### `struct NamedGradientStop`
```rust
pub struct NamedGradientStop {
    pub position: f32,
    pub name: String,
}
```

#### `struct NamedGradientPayload`
```rust
pub struct NamedGradientPayload {
    pub signature: String,
    pub stop_count: u32,
    pub mode: u32,
    pub scalar_1: f32,
    pub scalar_2: f32,
    pub scalar_3: f32,
    pub scalar_4: f32,
    pub scalar_5: f32,
    pub stops: Vec<NamedGradientStop>,
}
```

### Public Methods & API
- **`pub fn inferred_kind_name(&self) -> &'static str`**
- **`pub fn inferred_role_for_referenced_part(&self, referenced_part: u16) -> &'static str`**
- **`pub fn build_iconstack_root_style_list(entries: &[IconStackRootStyleEntry]) -> Vec<u8>`**
- **`pub fn parse_iconstack_root_style_list(raw: &[u8]) -> Result<Vec<IconStackRootStyleEntry>, &'static str>`**
- **`pub fn parse_iconstack_aux_list(raw: &[u8]) -> Result<Vec<IconStackAuxEntry>, &'static str>`**
- **`pub fn parse_named_gradient_payload(raw: &[u8]) -> Result<NamedGradientPayload, &'static str>`**
- **`pub fn IconStackError() -> ()`**
- **`pub fn IconStackRootStyleList() -> ()`**
- **`pub fn IconStackAuxList() -> ()`**
- **`pub fn build_iconstack_aux_list() -> ()`**
- **`pub fn build_iconstack_group_style_reference() -> ()`**
- **`pub fn parse_iconstack_group_style_reference() -> ()`**
- **`pub fn build_named_gradient_payload() -> ()`**
- **`pub fn inferred_name_kind() -> ()`**

---

## 📦 Module `actool::assets::imagestack`
- **Source File**: `actool/src/assets/imagestack.rs`
- **Lines of Code**: 117 LOC

### Structs & Binary Types
#### `struct StackLayerImage`
```rust
pub struct StackLayerImage {
    pub layer_name: String,
    pub filename: String,
    pub png_bytes: Vec<u8>,
}
```

### Public Methods & API
- **`pub fn build_stack_root_csi(canvas_w: u32, canvas_h: u32, layer_identifiers: &[u16],) -> Vec<u8>`**
- **`pub fn composite_source_over(layers_bgra: &[Vec<u8>], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn _csi_header() -> ()`**
- **`pub fn tlv_layer_list() -> ()`**
- **`pub fn tlv_stack_flags() -> ()`**
- **`pub fn tlv_stack_aux() -> ()`**
- **`pub fn tlv_uti() -> ()`**
- **`pub fn _lzfse_compress() -> ()`**
- **`pub fn cbck_container() -> ()`**
- **`pub fn _premultiplied_bgra_from_pngs() -> ()`**
- **`pub fn build_flattened_payload() -> ()`**
- **`pub fn build_radiosity_payload() -> ()`**
- **`pub fn _image_tlvs() -> ()`**
- **`pub fn build_flattened_csi() -> ()`**
- **`pub fn build_radiosity_csi() -> ()`**
- **`pub fn imagestack_renditions() -> ()`**

---

## 📦 Module `actool::assets::media`
- **Source File**: `actool/src/assets/media.rs`
- **Lines of Code**: 129 LOC

### Enums & Classification Types
#### `enum MediaType`
```rust
pub enum MediaType {
    Image,
    AudioCompressed,
    // mp3,
    m4a,
    aac (already compressed,
    pass-through)
    AudioUncompressed,
    // wav,
    caf (compress with LZFSE)
    Video,
    // mp4,
    mov,
    m4v (pass-through)
    Pdf,
    // pdf vector document
    VectorSvg,
    // svg
    Model3D,
    // usdz,
    obj,
    gltf,
    reality
    JsonLottie,
    // json,
    lottie
    BinaryData,
}
```

### Public Methods & API
- **`pub fn calculate_shannon_entropy(data: &[u8]) -> f64`**
- **`pub fn detect_media_type(filename: &str, data: &[u8]) -> MediaType`**
- **`pub fn select_optimal_compression(filename: &str, data: &[u8], width: u32, height: u32,) -> (Vec<u8>, &'static str)`**
- **`pub fn get_media_optimization_report(filename: &str, data: &[u8]) -> serde_json::Value`**

---

## 📦 Module `actool::assets::model3d`
- **Source File**: `actool/src/assets/model3d.rs`
- **Lines of Code**: 131 LOC

### Overview
Tangent-space Normal Map Compression (packs Nx, Ny into 2 channels for Metal GPU)
Generates mipmap chain levels for 3D textures

### Structs & Binary Types
#### `struct PBRMaterialMap`
```rust
pub struct PBRMaterialMap {
    pub name: String,
    pub width: u32,
    pub height: u32,
    pub occlusion: Vec<u8>,
    pub roughness: Vec<u8>,
    pub metallic: Vec<u8>,
}
```

### Public Methods & API
- **`pub fn new(name: &str, width: u32, height: u32) -> Self`**
- **`pub fn pack_orm_texture(&self) -> Vec<u8>`**
- **`pub fn compress_orm_payload(&self) -> Vec<u8>`**
- **`pub fn compress_normal_map_2channel(normal_rgb: &[u8], width: u32, height: u32,) -> Vec<u8>`**
- **`pub fn generate_mipmap_chain(bgra: &[u8], width: u32, height: u32,) -> Vec<(u32, u32, Vec<u8>)>`**

---

## 📦 Module `actool::assets::packed`
- **Source File**: `actool/src/assets/packed.rs`
- **Lines of Code**: 236 LOC

### Structs & Binary Types
#### `struct ShelfPackRegion`
```rust
pub struct ShelfPackRegion {
    pub x: u32,
    pub y: u32,
    pub width: u32,
    pub height: u32,
    pub rendition_index: usize,
}
```

### Public Methods & API
- **`pub fn atlas_name(opaque: bool, gray: bool) -> String`**
- **`pub fn _decode_deepmap_pixels(csi: &[u8]) -> Option<(u32, u32, Vec<u8>)>`**
- **`pub fn _classify(bgra: &[u8]) -> (bool, bool)`**
- **`pub fn is_pack_candidate(rendition: &AssetRendition) -> bool`**
- **`pub fn _shelf_pack(items: &[(usize, u32, u32)], max_width: u32,) -> (u32, u32, Vec<ShelfPackRegion>)`**
- **`pub fn _link_tail(page: u16) -> Vec<u8>`**
- **`pub fn _csi_link(x: u32, y: u32, w: u32, h: u32, page: u16) -> Vec<u8>`**
- **`pub fn _csi_link_full(source_csi: &[u8], x: u32, y: u32, w: u32, h: u32, page: u16) -> Vec<u8>`**
- **`pub fn build_link_tlv(x: u32, y: u32, w: u32, h: u32, page: u16) -> Vec<u8>`**
- **`pub fn pack_at(atlas_w: u32, _atlas_h: u32, items: &[(usize, u32, u32)]) -> (u32, u32, Vec<ShelfPackRegion>)`**
- **`pub fn atlas_score(efficiency: f32) -> f32`**
- **`pub fn composite_atlas(_regions: &[ShelfPackRegion], _renditions: &[AssetRendition], atlas_w: u32, atlas_h: u32) -> Vec<u8>`**
- **`pub fn _paginate_and_pack(renditions: Vec<AssetRendition>) -> Vec<AssetRendition>`**
- **`pub fn _atlas_palette(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn _atlas_mini_isa(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn _encode_zero_run(count: usize) -> Vec<u8>`**
- **`pub fn _encode_zero_run_cont(count: usize) -> Vec<u8>`**
- **`pub fn _atlas_dmp2(bgra: &[u8], width: u32, height: u32) -> Vec<u8>`**
- **`pub fn _csi_atlas(bgra: &[u8], width: u32, height: u32, name: &str) -> Vec<u8>`**
- **`pub fn pack_renditions(renditions: Vec<AssetRendition>) -> Vec<AssetRendition>`**

---

## 📦 Module `actool::assets::pdfcar`
- **Source File**: `actool/src/assets/pdfcar.rs`
- **Lines of Code**: 10 LOC

### Public Methods & API
- **`pub fn build_pdf_fallback_car(_name: &str) -> Vec<u8>`**
- **`pub fn main() -> ()`**

---

## 📦 Module `actool::assets::solidstack`
- **Source File**: `actool/src/assets/solidstack.rs`
- **Lines of Code**: 199 LOC

### Structs & Binary Types
#### `struct SolidImageStackReferencedKey`
```rust
pub struct SolidImageStackReferencedKey {
    pub attribute_value_pairs: Vec<(u16,
    u16)>,
}
```

#### `struct SolidImageStackLayerReference`
```rust
pub struct SolidImageStackLayerReference {
    pub origin_x: u32,
    pub origin_y: u32,
    pub reserved0: u32,
    pub width: u32,
    pub height: u32,
    pub reserved1: u32,
    pub opacity: f32,
    pub referenced_key: SolidImageStackReferencedKey,
}
```

#### `struct SolidImageStackLayerFlag`
```rust
pub struct SolidImageStackLayerFlag {
    pub reserved0: [u8; 8],
    pub enabled: u8,
    pub reserved1: [u8; 4],
}
```

#### `struct SolidImageStackLayerReserved`
```rust
pub struct SolidImageStackLayerReserved {
    pub raw: [u8; 20],
}
```

### Enums & Classification Types
#### `enum SolidImageStackError`
```rust
pub enum SolidImageStackError {
    #[error("Solid image stack data is truncated or invalid")]
    Truncated,
    #[error("Nonzero reserved field or length mismatch")]
    InvalidReserved,
}
```

### Public Methods & API
- **`pub fn build_solidimagestack_layer_list(references: &[SolidImageStackLayerReference]) -> Vec<u8>`**
- **`pub fn build_solidimagestack_layer_flags(flags: &[SolidImageStackLayerFlag]) -> Vec<u8>`**
- **`pub fn build_solidimagestack_layer_reserved(entries: &[SolidImageStackLayerReserved]) -> Vec<u8>`**
- **`pub fn parse_solidimagestack_layer_list(data: &[u8]) -> Result<Vec<SolidImageStackLayerReference>, SolidImageStackError>`**
- **`pub fn parse_solidimagestack_layer_flags(data: &[u8]) -> Result<Vec<SolidImageStackLayerFlag>, SolidImageStackError>`**
- **`pub fn parse_solidimagestack_layer_reserved(data: &[u8]) -> Result<Vec<SolidImageStackLayerReserved>, SolidImageStackError>`**
- **`pub fn SolidImageStackLayerList() -> ()`**
- **`pub fn SolidImageStackLayerFlags() -> ()`**
- **`pub fn SolidImageStackLayerReservedList() -> ()`**

---

## 📦 Module `actool::assets::texture`
- **Source File**: `actool/src/assets/texture.rs`
- **Lines of Code**: 101 LOC

### Structs & Binary Types
#### `struct TextureReference`
```rust
pub struct TextureReference {
    pub payload_value: u32,
    pub reserved0: u32,
    pub u32_2: u32,
    pub u32_3: u32,
    pub u32_4: u32,
    pub key_pairs: Vec<(u16,
    u16)>,
}
```

#### `struct TextureAuxiliaryFlag`
```rust
pub struct TextureAuxiliaryFlag {
    pub raw: [u8; 12],
    pub values: (u32,
    u32,
    u32),
}
```

### Enums & Classification Types
#### `enum TextureRenditionError`
```rust
pub enum TextureRenditionError {
    #[error("Invalid texture payload or header")]
    InvalidHeader,
    #[error("Payload is truncated")]
    Truncated,
}
```

### Public Methods & API
- **`pub fn build_texture_reference_payload(reference: &TextureReference) -> Vec<u8>`**
- **`pub fn build_texture_auxiliary_flag(flag: &TextureAuxiliaryFlag) -> Vec<u8>`**
- **`pub fn parse_texture_reference_payload(data: &[u8]) -> Result<TextureReference, TextureRenditionError>`**
- **`pub fn parse_texture_auxiliary_flag(data: &[u8]) -> Result<TextureAuxiliaryFlag, TextureRenditionError>`**

---

## 📦 Module `actool::assets::texture_gradient_stack`
- **Source File**: `actool/src/assets/texture_gradient_stack.rs`
- **Lines of Code**: 189 LOC

### Structs & Binary Types
#### `struct TextureReference`
```rust
pub struct TextureReference {
    pub texture_name: String,
    pub width: u32,
    pub height: u32,
    pub key_pairs: Vec<(u16,
    u16)>,
    pub payload_value: u32,
    pub u32_2: u32,
    pub u32_3: u32,
    pub u32_4: u32,
}
```

#### `struct GradientStop`
```rust
pub struct GradientStop {
    pub position: f32,
    pub color_r: f32,
    pub color_g: f32,
    pub color_b: f32,
    pub color_a: f32,
    pub name: Option<String>,
}
```

#### `struct NamedGradient`
```rust
pub struct NamedGradient {
    pub name: String,
    pub gradient_type: u32,
    pub stops: Vec<GradientStop>,
    pub start_point: (f32,
    f32),
    pub end_point: (f32,
    f32),
}
```

### Public Methods & API
- **`pub fn new(texture_name: &str, width: u32, height: u32) -> Self`**
- **`pub fn add_key_pair(&mut self, attribute: u16, value: u16) -> ()`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn new(name: &str, gradient_type: u32) -> Self`**
- **`pub fn add_stop(&mut self, stop: GradientStop) -> ()`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn create_linear_gradient(name: &str, start_color: (f32, f32, f32, f32), end_color: (f32, f32, f32, f32)) -> NamedGradient`**
- **`pub fn create_radial_gradient(name: &str, inner_color: (f32, f32, f32, f32), outer_color: (f32, f32, f32, f32)) -> NamedGradient`**
- **`pub fn IconStackLayer() -> ()`**
- **`pub fn IconStackRenderingProperties() -> ()`**
- **`pub fn IconStack() -> ()`**
- **`pub fn create_simple_icon_stack() -> ()`**
- **`pub fn deserialize() -> ()`**
- **`pub fn set_bounds() -> ()`**
- **`pub fn add_referenced_key() -> ()`**
- **`pub fn add_entry() -> ()`**
- **`pub fn add_layer() -> ()`**
- **`pub fn set_rendering_properties() -> ()`**
- **`pub fn add_auxiliary_data() -> ()`**

---

## 📦 Module `actool::assets::thinning`
- **Source File**: `actool/src/assets/thinning.rs`
- **Lines of Code**: 96 LOC

### Structs & Binary Types
#### `struct ThinningOptions`
```rust
pub struct ThinningOptions {
    pub idiom: Option<String>,
    pub scale: Option<u16>,
    pub appearance: Option<u16>,
    pub localization: Option<String>,
    pub keep_fallbacks: bool,
}
```

### Public Methods & API
- **`pub fn new() -> Self`**
- **`pub fn idiom_id(&self) -> Option<u16>`**
- **`pub fn metadata_arguments(&self) -> String`**
- **`pub fn thin_renditions(renditions: Vec<AssetRendition>, options: &ThinningOptions) -> Vec<AssetRendition>`**

---

