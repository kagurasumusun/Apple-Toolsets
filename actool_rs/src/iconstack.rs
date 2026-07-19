#[derive(Debug, Clone)]
pub struct IconStackRootStyleEntry {
    pub kind: u32,
    pub value: f32,
    pub enabled: u32,
    pub reserved_hex: String,
}

impl IconStackRootStyleEntry {
    pub fn inferred_kind_name(&self) -> &'static str {
        match self.kind {
            0 => "fill-or-gradient",
            2 => "icon-group",
            _ => "unknown",
        }
    }
}
