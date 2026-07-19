use crate::hybrid_compression::hybrid_compress;

pub fn alpha_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
    hybrid_compress(bgra, width, height)
}
