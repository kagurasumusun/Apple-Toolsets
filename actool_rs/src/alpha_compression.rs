use crate::hybrid_compression::hybrid_compress_for_cbck;

pub fn alpha_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
    hybrid_compress_for_cbck(bgra, width, height)
}
