use crate::lzfse;

pub fn omega_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    lzfse::compress(bgra)
}
