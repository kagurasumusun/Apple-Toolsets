use byteorder::{LittleEndian, WriteBytesExt};

#[derive(Debug, Clone)]
pub struct IconStackRootStyleEntry {
    pub kind: u32,
    pub value: f32,
    pub enabled: u8,
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

    pub fn inferred_role_for_referenced_part(&self, referenced_part: u16) -> &'static str {
        match (self.kind, referenced_part) {
            (0, 217) => "named-color-fill",
            (0, 247) => "named-gradient-fill",
            (2, 246) => "icon-group-depth",
            _ => "unknown",
        }
    }
}

#[derive(Debug, Clone)]
pub struct IconStackAuxEntry {
    pub u32_1: u32,
    pub f32_1: f32,
    pub u32_2: u32,
    pub f32_2: f32,
    pub u32_3: u32,
}

#[derive(Debug, Clone)]
pub struct IconStackGroupStyleReference {
    pub count: u32,
    pub kind: u32,
    pub name: String,
}

#[derive(Debug, Clone)]
pub struct NamedGradientStop {
    pub position: f32,
    pub name: String,
}

#[derive(Debug, Clone)]
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

pub fn build_iconstack_root_style_list(entries: &[IconStackRootStyleEntry]) -> Vec<u8> {
    let mut out = Vec::new();
    let _ = out.write_u32::<LittleEndian>(entries.len() as u32);
    let _ = out.write_u32::<LittleEndian>(0);

    for entry in entries {
        let _ = out.write_u32::<LittleEndian>(entry.kind);
        let _ = out.write_f32::<LittleEndian>(entry.value);
        out.push(entry.enabled);

        let hex_bytes = hex::decode(&entry.reserved_hex).unwrap_or_else(|_| vec![0u8; 4]);
        out.extend_from_slice(&hex_bytes[..4]);
    }

    out
}

pub fn parse_named_gradient_payload(raw: &[u8]) -> Result<NamedGradientPayload, &'static str> {
    if raw.len() < 40 {
        return Err("Named gradient payload is truncated");
    }

    let signature = String::from_utf8_lossy(&raw[0..4]).to_string();
    let stop_count = u32::from_le_bytes(raw[4..8].try_into().unwrap());
    let mode = u32::from_le_bytes(raw[8..12].try_into().unwrap());

    let scalar_1 = f32::from_le_bytes(raw[12..16].try_into().unwrap());
    let scalar_2 = f32::from_le_bytes(raw[16..20].try_into().unwrap());
    let scalar_3 = f32::from_le_bytes(raw[20..24].try_into().unwrap());
    let scalar_4 = f32::from_le_bytes(raw[24..28].try_into().unwrap());
    let scalar_5 = f32::from_le_bytes(raw[28..32].try_into().unwrap());

    let mut cursor = 32;
    let mut stops = Vec::new();

    for _ in 0..stop_count {
        if cursor + 8 > raw.len() {
            break;
        }
        let pos = f32::from_le_bytes(raw[cursor..cursor + 4].try_into().unwrap());
        let name_len = u32::from_le_bytes(raw[cursor + 4..cursor + 8].try_into().unwrap()) as usize;
        cursor += 8;

        if cursor + name_len > raw.len() {
            break;
        }
        let name_raw = &raw[cursor..cursor + name_len];
        cursor += name_len;

        let name = String::from_utf8_lossy(name_raw.strip_suffix(b"\0").unwrap_or(name_raw)).to_string();
        stops.push(NamedGradientStop { position: pos, name });
    }

    Ok(NamedGradientPayload {
        signature,
        stop_count,
        mode,
        scalar_1,
        scalar_2,
        scalar_3,
        scalar_4,
        scalar_5,
        stops,
    })
}
