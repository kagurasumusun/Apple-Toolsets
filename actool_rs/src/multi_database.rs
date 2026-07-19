use crate::bom::BOMStore;
use std::collections::HashMap;

pub struct MultiDatabaseCAR {
    pub coreui_version: u32,
    pub databases: HashMap<String, BOMStore>,
}

impl MultiDatabaseCAR {
    pub fn new(coreui_version: u32) -> Self {
        Self {
            coreui_version,
            databases: HashMap::new(),
        }
    }
}
