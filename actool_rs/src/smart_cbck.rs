use crate::cbck::encode_cbck;

pub struct SmartCBCKEncoder {
    pub clean_alpha: bool,
}

impl SmartCBCKEncoder {
    pub fn new(clean_alpha: bool) -> Self {
        Self { clean_alpha }
    }

    pub fn encode(&self, bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
        encode_cbck(bgra, width, height, 4, self.clean_alpha)
    }
}
