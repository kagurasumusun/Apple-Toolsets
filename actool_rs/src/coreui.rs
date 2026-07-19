#[derive(Debug, Clone)]
pub struct CoreUIProfile {
    pub dialect: String,
    pub core_ui_version: u32,
    pub storage_version: u32,
    pub program_tag: String,
}

pub fn resolve_profile(platform: &str) -> CoreUIProfile {
    match platform {
        "macosx" | "mac" => CoreUIProfile {
            dialect: "coreui-975-macos".to_string(),
            core_ui_version: 975,
            storage_version: 1,
            program_tag: "975 [LAR]".to_string(),
        },
        _ => CoreUIProfile {
            dialect: "coreui-975-device".to_string(),
            core_ui_version: 975,
            storage_version: 1,
            program_tag: "975".to_string(),
        },
    }
}
