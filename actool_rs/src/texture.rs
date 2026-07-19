use byteorder::{LittleEndian, WriteBytesExt};

#[derive(Debug, Clone)]
pub struct TextureReference {
    pub payload_value: u32,
    pub reserved0: u32,
    pub u32_2: u32,
    pub u32_3: u32,
    pub u32_4: u32,
    pub key_pairs: Vec<(u16, u16)>,
}

pub fn build_texture_reference_payload(reference: &TextureReference) -> Vec<u8> {
    let mut pairs = Vec::new();
    for (attr, val) in &reference.key_pairs {
        let _ = pairs.write_u16::<LittleEndian>(*attr);
        let _ = pairs.write_u16::<LittleEndian>(*val);
    }

    let mut out = Vec::new();
    out.extend_from_slice(b"RTXT");
    let _ = out.write_u32::<LittleEndian>(reference.reserved0);
    let _ = out.write_u32::<LittleEndian>(reference.payload_value);
    let _ = out.write_u32::<LittleEndian>(reference.u32_2);
    let _ = out.write_u32::<LittleEndian>(reference.u32_3);
    let _ = out.write_u32::<LittleEndian>(reference.u32_4);
    let _ = out.write_u32::<LittleEndian>(pairs.len() as u32);
    let _ = out.write_u32::<LittleEndian>(0);
    out.extend_from_slice(&pairs);

    out
}
