use crate::bom::BOMStore;
use crate::car::CARFile;
use serde_json::{json, Value};
use std::path::Path;

pub fn inspect<P: AsRef<Path>>(path: P) -> Result<Value, String> {
    let store = BOMStore::from_path(path).map_err(|e| e.to_string())?;
    let car = CARFile::from_bom_store(&store).map_err(|e| e.to_string())?;

    Ok(json!({
        "byte_order": car.header.byte_order,
        "core_ui_version": car.header.core_ui_version,
        "storage_version": car.header.storage_version,
        "rendition_count": car.header.rendition_count,
        "identifier": car.header.identifier,
        "allocated_blocks": car.block_count
    }))
}
