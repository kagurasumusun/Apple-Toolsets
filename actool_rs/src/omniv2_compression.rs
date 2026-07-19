use crate::lzfse;

pub fn omniv2_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    lzfse::compress(bgra)
}
