use crate::lzfse;

pub fn tet_ultimate_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    lzfse::compress(bgra)
}
