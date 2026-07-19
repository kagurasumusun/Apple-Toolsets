pub struct ZeroCodeDatabase {
    pub name: String,
    pub records: Vec<Vec<u8>>,
}

impl ZeroCodeDatabase {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            records: Vec::new(),
        }
    }
}
