use byteorder::{LittleEndian, WriteBytesExt};

#[derive(Debug, Clone)]
pub struct ZeroCodeLayer {
    pub name: String,
    pub opacity: f32,
}

impl ZeroCodeLayer {
    pub fn serialize(&self) -> Vec<u8> {
        let mut out = Vec::new();
        let name_bytes = self.name.as_bytes();
        let _ = out.write_u32::<LittleEndian>(name_bytes.len() as u32);
        out.extend_from_slice(name_bytes);
        let _ = out.write_f32::<LittleEndian>(self.opacity);
        out
    }
}

#[derive(Debug, Clone)]
pub struct ZeroCodeEffect {
    pub effect_type: u32,
    pub radius: f32,
}

impl ZeroCodeEffect {
    pub fn serialize(&self) -> Vec<u8> {
        let mut out = Vec::new();
        let _ = out.write_u32::<LittleEndian>(self.effect_type);
        let _ = out.write_f32::<LittleEndian>(self.radius);
        out
    }
}

#[derive(Debug, Clone)]
pub struct ZeroCodeBezel {
    pub name: String,
    pub width: u32,
    pub height: u32,
    pub layers: Vec<ZeroCodeLayer>,
    pub effects: Vec<ZeroCodeEffect>,
}

impl ZeroCodeBezel {
    pub fn new(name: &str, width: u32, height: u32) -> Self {
        Self {
            name: name.to_string(),
            width,
            height,
            layers: Vec::new(),
            effects: Vec::new(),
        }
    }

    pub fn serialize(&self) -> Vec<u8> {
        let mut out = Vec::new();
        let name_bytes = self.name.as_bytes();

        let _ = out.write_u32::<LittleEndian>(name_bytes.len() as u32);
        out.extend_from_slice(name_bytes);
        let _ = out.write_u32::<LittleEndian>(self.width);
        let _ = out.write_u32::<LittleEndian>(self.height);

        let _ = out.write_u32::<LittleEndian>(self.layers.len() as u32);
        for l in &self.layers {
            out.extend_from_slice(&l.serialize());
        }

        let _ = out.write_u32::<LittleEndian>(self.effects.len() as u32);
        for e in &self.effects {
            out.extend_from_slice(&e.serialize());
        }

        out
    }
}
