use std::collections::HashMap;

pub struct FacetHashLookup {
    pub lookup_table: HashMap<String, String>,
}

impl Default for FacetHashLookup {
    fn default() -> Self {
        Self::new()
    }
}

impl FacetHashLookup {
    pub fn new() -> Self {
        Self {
            lookup_table: HashMap::new(),
        }
    }

    pub fn lookup(&self, hash_pattern: &str) -> Option<&String> {
        self.lookup_table.get(hash_pattern)
    }
}
