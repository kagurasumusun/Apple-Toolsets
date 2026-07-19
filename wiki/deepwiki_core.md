# 🧬 DeepWiki Module Specification: Core Binary & Storage Engine (`actool::core`)

Comprehensive architectural and algorithmic breakdown for all **11** modules in the `core` domain layer.

--- 

## 📦 Module `actool::core::bom`
- **Source File**: `actool/src/core/bom.rs`
- **Lines of Code**: 218 LOC

### Structs & Binary Types
#### `struct BOMHeader`
```rust
pub struct BOMHeader {
    pub version: u32,
    pub block_count_hint: u32,
    pub index_offset: usize,
    pub index_length: usize,
    pub variables_offset: usize,
    pub variables_length: usize,
}
```

#### `struct Block`
```rust
pub struct Block {
    pub identifier: u32,
    pub offset: usize,
    pub length: usize,
}
```

#### `struct BOMStore`
```rust
pub struct BOMStore {
    pub data: Vec<u8>,
    pub header: BOMHeader,
    pub blocks: HashMap<u32,
    Block>,
    pub variables: HashMap<String,
    u32>,
}
```

### Enums & Classification Types
#### `enum BOMError`
```rust
pub enum BOMError {
    #[error("File is shorter than 32-byte BOM header")]
    TruncatedHeader,
    #[error("Invalid BOM magic: {0:?,
}
```

### Public Methods & API
- **`pub fn from_bytes(data: Vec<u8>) -> Result<Self, BOMError>`**
- **`pub fn _read_header(&self) -> &BOMHeader`**
- **`pub fn _read_block_index(&self) -> &HashMap<u32, Block>`**
- **`pub fn _read_variables(&self) -> &HashMap<String, u32>`**
- **`pub fn get_databases(&self) -> HashMap<String, u32>`**
- **`pub fn has_database(&self, name: &str) -> bool`**
- **`pub fn block_data(&self, identifier: u32) -> Result<&[u8], BOMError>`**
- **`pub fn named_block_data(&self, name: &str) -> Result<&[u8], BOMError>`**

---

## 📦 Module `actool::core::bomwriter`
- **Source File**: `actool/src/core/bomwriter.rs`
- **Lines of Code**: 117 LOC

### Structs & Binary Types
#### `struct PendingBlock`
```rust
pub struct PendingBlock {
    pub id: u32,
    pub data: Vec<u8>,
    pub name: Option<String>,
}
```

#### `struct BOMWriter`
```rust
pub struct BOMWriter {
    pub blocks: Vec<PendingBlock>,
    pub next_id: u32,
}
```

### Public Methods & API
- **`pub fn new() -> Self`**
- **`pub fn _align(offset: usize, alignment: usize) -> usize`**
- **`pub fn add_block(&mut self, data: Vec<u8>, name: Option<String>) -> u32`**
- **`pub fn replace_block(&mut self, id: u32, new_data: Vec<u8>) -> bool`**
- **`pub fn build(&self) -> Vec<u8>`**

---

## 📦 Module `actool::core::car`
- **Source File**: `actool/src/core/car.rs`
- **Lines of Code**: 374 LOC

### Structs & Binary Types
#### `struct CARHeader`
```rust
pub struct CARHeader {
    pub byte_order: String,
    pub core_ui_version: u32,
    pub storage_version: u32,
    pub storage_timestamp: u32,
    pub rendition_count: u32,
    pub schema_version: u32,
    pub main_version: String,
    pub version_string: String,
    pub identifier: String,
    pub associated_checksum: u32,
    pub color_space_id: u32,
    pub key_semantics: u32,
}
```

#### `struct ExtendedMetadata`
```rust
pub struct ExtendedMetadata {
    pub authoring_tool: String,
}
```

#### `struct Facet`
```rust
pub struct Facet {
    pub name: String,
    pub cursor_hotspot: (u16,
    u16),
    pub attributes: Vec<(u16,
    u16)>,
}
```

#### `struct NamedValueRegistryEntry`
```rust
pub struct NamedValueRegistryEntry {
    pub name: String,
    pub value: u16,
}
```

#### `struct KeyFormat`
```rust
pub struct KeyFormat {
    pub byte_order: String,
    pub attributes: Vec<u32>,
}
```

#### `struct Rendition`
```rust
pub struct Rendition {
    pub key_values: Vec<u16>,
    pub key: HashMap<String,
    u16>,
    pub csi: CSIHeader,
}
```

#### `struct CARFile`
```rust
pub struct CARFile {
    pub header: CARHeader,
    pub key_format: KeyFormat,
    pub block_count: usize,
    pub facets: Vec<Facet>,
    pub renditions: Vec<Rendition>,
}
```

### Public Methods & API
- **`pub fn named_attributes(&self) -> HashMap<String, u16>`**
- **`pub fn names(&self) -> Vec<String>`**
- **`pub fn _cstring(raw: &[u8]) -> String`**
- **`pub fn parse_extended_metadata(raw: &[u8]) -> Result<ExtendedMetadata, BOMError>`**
- **`pub fn parse_facet(name_raw: &[u8], value_raw: &[u8]) -> Result<Facet, BOMError>`**
- **`pub fn parse_named_value_registry_entry(key_raw: &[u8], value_raw: &[u8],) -> Result<NamedValueRegistryEntry, BOMError>`**
- **`pub fn parse_rendition(key_raw: &[u8], value_raw: &[u8], key_format: &KeyFormat,) -> Result<Rendition, BOMError>`**
- **`pub fn parse_car_header(data: &[u8]) -> Result<CARHeader, BOMError>`**
- **`pub fn parse_key_format(data: &[u8]) -> Result<KeyFormat, BOMError>`**
- **`pub fn from_bom_store(store: &BOMStore) -> Result<Self, BOMError>`**

---

## 📦 Module `actool::core::carinfo`
- **Source File**: `actool/src/core/carinfo.rs`
- **Lines of Code**: 124 LOC

### Public Methods & API
- **`pub fn decoded_tlvs(data: &[u8]) -> Vec<Value>`**
- **`pub fn decoded_payload(data: &[u8]) -> Value`**
- **`pub fn _decoded_tlvs() -> ()`**
- **`pub fn _decoded_payload() -> ()`**

---

## 📦 Module `actool::core::carwriter`
- **Source File**: `actool/src/core/carwriter.rs`
- **Lines of Code**: 336 LOC

### Structs & Binary Types
#### `struct AssetRendition`
```rust
pub struct AssetRendition {
    pub name: String,
    pub filename: String,
    pub csi_bytes: Vec<u8>,
    pub identifier: u16,
    pub idiom: u16,
    pub scale: u16,
    pub gamut: u16,
    pub appearance: u16,
    pub width: u32,
    pub height: u32,
}
```

#### `struct CARWriter`
```rust
pub struct CARWriter {
    pub renditions: Vec<AssetRendition>,
    pub platform: String,
}
```

### Public Methods & API
- **`pub fn _fixed(value: f32) -> u32`**
- **`pub fn fixed(value: f32) -> u32`**
- **`pub fn _identifier(name: &str) -> u16`**
- **`pub fn identifier(name: &str) -> u16`**
- **`pub fn _localization_identifier(name: &str) -> u16`**
- **`pub fn localization_identifier(name: &str) -> u16`**
- **`pub fn _select_key_attributes(platform: &str) -> &'static [u16]`**
- **`pub fn select_key_attributes(platform: &str) -> &'static [u16]`**
- **`pub fn _car_header(core_ui_version: u32, rendition_count: u32, main_version: &str) -> Vec<u8>`**
- **`pub fn _extended_metadata(author: &str, platform: &str, target: &str) -> Vec<u8>`**
- **`pub fn _key_format(attributes: &[u16]) -> Vec<u8>`**
- **`pub fn _tree_descriptor(root_block: u32, node_size: u32, record_count: u32, key_size: u32) -> Vec<u8>`**
- **`pub fn _leaf(writer: &mut BOMWriter, items: &[(&AssetRendition, u32)]) -> Vec<u8>`**
- **`pub fn _add_multilevel_tree(writer: &mut BOMWriter, tree_name: &str, items: &[(&AssetRendition, u32)]) -> ()`**
- **`pub fn _rendition_key(r: &AssetRendition) -> Vec<u8>`**
- **`pub fn new(platform: &str) -> Self`**
- **`pub fn add_rendition(&mut self, rendition: AssetRendition) -> ()`**
- **`pub fn add_png_image(&mut self, name: &str, bgra: &[u8], width: u32, height: u32, scale: u16, idiom: u16, ident: u16,) -> ()`**
- **`pub fn add_color(&mut self, name: &str, r: f32, g: f32, b: f32, a: f32, ident: u16,) -> ()`**
- **`pub fn build(&self) -> Vec<u8>`**
- **`pub fn _csi_color(r: f32, g: f32, b: f32, a: f32) -> Vec<u8>`**
- **`pub fn build_assets_car(renditions: Vec<AssetRendition>, platform: &str) -> Vec<u8>`**
- **`pub fn _gray_ga_bytes(bgra: &[u8]) -> Vec<u8>`**
- **`pub fn _csi_data(data: &[u8], name: &str) -> Vec<u8>`**
- **`pub fn data_rendition(name: &str, data: &[u8]) -> AssetRendition`**

---

## 📦 Module `actool::core::coreui`
- **Source File**: `actool/src/core/coreui.rs`
- **Lines of Code**: 92 LOC

### Structs & Binary Types
#### `struct CoreUIProfile`
```rust
pub struct CoreUIProfile {
    pub name: String,
    pub header_version: u32,
    pub header_field2: u32,
    pub project_tag: String,
    pub header_tail: (u32,
    u32,
    u32,
    u32),
    pub apple_agent_token: String,
}
```

### Public Methods & API
- **`pub fn program_string(&self) -> String`**
- **`pub fn writer_comment(&self) -> &'static str`**
- **`pub fn profile_for_platform(platform: Option<&str>) -> CoreUIProfile`**
- **`pub fn auto_select_profile(platform: Option<&str>, target: Option<&str>) -> CoreUIProfile`**
- **`pub fn resolve_profile(profile_name: Option<&str>, platform: Option<&str>) -> CoreUIProfile`**

---

## 📦 Module `actool::core::csi`
- **Source File**: `actool/src/core/csi.rs`
- **Lines of Code**: 281 LOC

### Structs & Binary Types
#### `struct CSIHeader`
```rust
pub struct CSIHeader {
    pub magic: [u8; 4],
    pub version: u32,
    pub flags: u32,
    pub width: u32,
    pub height: u32,
    pub scale: u32,
    pub pixel_format: [u8; 4],
    pub color_space_id: u32,
    pub layout: u32,
    pub name: String,
    pub tlvs: Vec<TLV>,
    pub rendition_data: Vec<u8>,
}
```

#### `struct TLV`
```rust
pub struct TLV {
    pub tag: u32,
    pub value: Vec<u8>,
}
```

### Public Methods & API
- **`pub fn parse_csi(data: &[u8]) -> Result<CSIHeader, crate::bom::BOMError>`**
- **`pub fn build_tlv(tag: u32, value: &[u8]) -> Vec<u8>`**
- **`pub fn make_adaptive_csi(bgra: &[u8], width: u32, height: u32, filename: &str, scale: u32, optimize_mode: Option<&str>,) -> Vec<u8>`**
- **`pub fn build_csi_png(bgra: &[u8], width: u32, height: u32, filename: &str, scale: u32, prefer_cbck: bool,) -> Vec<u8>`**

---

## 📦 Module `actool::core::facet_hash_lookup`
- **Source File**: `actool/src/core/facet_hash_lookup.rs`
- **Lines of Code**: 68 LOC

### Structs & Binary Types
#### `struct FacetHashLookupTable`
```rust
pub struct FacetHashLookupTable {
    pub lookup_table: HashMap<u32,
    u16>,
}
```

### Public Methods & API
- **`pub fn new() -> Self`**
- **`pub fn compute_polynomial_hash(name: &str) -> u32`**
- **`pub fn lookup(&self, name: &str) -> u16`**
- **`pub fn has_entry(&self, name: &str) -> bool`**
- **`pub fn build_lookup_table() -> ()`**
- **`pub fn _load_table() -> ()`**

---

## 📦 Module `actool::core::multi_database`
- **Source File**: `actool/src/core/multi_database.rs`
- **Lines of Code**: 119 LOC

### Structs & Binary Types
#### `struct MultiDatabaseCAR`
```rust
pub struct MultiDatabaseCAR {
    pub coreui_version: u32,
    pub databases: HashMap<String,
    BOMStore>,
    pub main_store: Option<BOMStore>,
    pub database_names: Vec<String>,
}
```

### Public Methods & API
- **`pub fn new(coreui_version: u32) -> Self`**
- **`pub fn get_database(&self, name: &str) -> Option<&BOMStore>`**
- **`pub fn has_database(&self, name: &str) -> bool`**
- **`pub fn get_all_databases(&self) -> &HashMap<String, BOMStore>`**
- **`pub fn get_image_renditions(&self) -> Vec<Vec<u8>>`**
- **`pub fn get_color_definitions(&self) -> HashMap<String, Vec<u8>>`**
- **`pub fn get_facet_keys(&self) -> HashMap<String, u32>`**
- **`pub fn validate_compatibility(&self) -> (bool, String)`**

---

## 📦 Module `actool::core::tree`
- **Source File**: `actool/src/core/tree.rs`
- **Lines of Code**: 98 LOC

### Structs & Binary Types
#### `struct TreeDescriptor`
```rust
pub struct TreeDescriptor {
    pub version: u32,
    pub root_block: u32,
    pub node_size: usize,
    pub path_count: u32,
}
```

#### `struct TreeEntry`
```rust
pub struct TreeEntry {
    pub key_block: u32,
    pub value_block: u32,
    pub key: Vec<u8>,
    pub value: Vec<u8>,
}
```

### Public Methods & API
- **`pub fn parse_descriptor(raw: &[u8]) -> Result<TreeDescriptor, BOMError>`**
- **`pub fn read_leaf_entries(store: &BOMStore, name: &str) -> Result<Vec<TreeEntry>, BOMError>`**

---

## 📦 Module `actool::core::zero_code_db`
- **Source File**: `actool/src/core/zero_code_db.rs`
- **Lines of Code**: 287 LOC

### Structs & Binary Types
#### `struct ZeroCodeLayer`
```rust
pub struct ZeroCodeLayer {
    pub name: String,
    pub opacity: f32,
    pub properties: HashMap<String,
    String>,
}
```

#### `struct ZeroCodeEffect`
```rust
pub struct ZeroCodeEffect {
    pub effect_type: u32,
    pub radius: f32,
    pub parameters: HashMap<String,
    f32>,
}
```

#### `struct ZeroCodePath`
```rust
pub struct ZeroCodePath {
    pub points: Vec<(f32,
    f32)>,
    pub is_closed: bool,
}
```

#### `struct ZeroCodeBezel`
```rust
pub struct ZeroCodeBezel {
    pub name: String,
    pub width: u32,
    pub height: u32,
    pub layers: Vec<ZeroCodeLayer>,
    pub effects: Vec<ZeroCodeEffect>,
}
```

#### `struct ZeroCodeGlyph`
```rust
pub struct ZeroCodeGlyph {
    pub name: String,
    pub width: u32,
    pub height: u32,
    pub paths: Vec<ZeroCodePath>,
}
```

#### `struct ZeroCodeDatabase`
```rust
pub struct ZeroCodeDatabase {
    pub name: String,
    pub bezels: HashMap<String,
    ZeroCodeBezel>,
    pub glyphs: HashMap<String,
    ZeroCodeGlyph>,
}
```

### Public Methods & API
- **`pub fn new(name: &str, opacity: f32) -> Self`**
- **`pub fn set_property(&mut self, key: &str, value: &str) -> ()`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn deserialize(data: &[u8], mut offset: usize) -> Result<(Self, usize), &'static str>`**
- **`pub fn new(effect_type: u32, radius: f32) -> Self`**
- **`pub fn set_parameter(&mut self, key: &str, value: f32) -> ()`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn deserialize(data: &[u8], mut offset: usize) -> Result<(Self, usize), &'static str>`**
- **`pub fn new(points: Vec<(f32, f32)>, is_closed: bool) -> Self`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn new(name: &str, width: u32, height: u32) -> Self`**
- **`pub fn add_layer(&mut self, layer: ZeroCodeLayer) -> ()`**
- **`pub fn add_effect(&mut self, effect: ZeroCodeEffect) -> ()`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn deserialize(data: &[u8]) -> Result<Self, &'static str>`**
- **`pub fn new(name: &str, width: u32, height: u32) -> Self`**
- **`pub fn add_path(&mut self, path: ZeroCodePath) -> ()`**
- **`pub fn serialize(&self) -> Vec<u8>`**
- **`pub fn new(name: &str) -> Self`**
- **`pub fn add_bezel(&mut self, bezel: ZeroCodeBezel) -> ()`**
- **`pub fn add_glyph(&mut self, glyph: ZeroCodeGlyph) -> ()`**
- **`pub fn get_bezel(&self, name: &str) -> Option<&ZeroCodeBezel>`**
- **`pub fn get_glyph(&self, name: &str) -> Option<&ZeroCodeGlyph>`**
- **`pub fn serialize_bezels(&self) -> Vec<u8>`**
- **`pub fn serialize_glyphs(&self) -> Vec<u8>`**

---

