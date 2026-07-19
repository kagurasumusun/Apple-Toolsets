use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct AssetModel {
    pub name: String,
    pub kind: String,
}
