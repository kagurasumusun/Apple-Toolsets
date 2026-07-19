use byteorder::{LittleEndian, WriteBytesExt};

#[derive(Debug, Clone)]
pub struct SolidImageStackLayerReference {
    pub origin_x: u32,
    pub origin_y: u32,
    pub reserved0: u32,
    pub width: u32,
    pub height: u32,
    pub reserved1: u32,
    pub opacity: f32,
    pub attribute_value_pairs: Vec<(u16, u16)>,
}

pub fn build_solidimagestack_layer_list(references: &[SolidImageStackLayerReference]) -> Vec<u8> {
    let mut out = Vec::new();
    let _ = out.write_u32::<LittleEndian>(references.len() as u32);
    let _ = out.write_u32::<LittleEndian>(0);

    for ref_item in references {
        let mut pairs = Vec::new();
        for (attr, val) in &ref_item.attribute_value_pairs {
            let _ = pairs.write_u16::<LittleEndian>(*attr);
            let _ = pairs.write_u16::<LittleEndian>(*val);
        }

        let _ = out.write_u32::<LittleEndian>(ref_item.origin_x);
        let _ = out.write_u32::<LittleEndian>(ref_item.origin_y);
        let _ = out.write_u32::<LittleEndian>(ref_item.reserved0);
        let _ = out.write_u32::<LittleEndian>(ref_item.width);
        let _ = out.write_u32::<LittleEndian>(ref_item.height);
        let _ = out.write_u32::<LittleEndian>(ref_item.reserved1);
        let _ = out.write_f32::<LittleEndian>(ref_item.opacity);
        let _ = out.write_u32::<LittleEndian>(pairs.len() as u32);
        out.extend_from_slice(&pairs);
    }

    out
}
