use crate::lzfse;

pub fn lpc_encode_apple_compat(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    // Quantize or process BGRA, then compress via LZFSE
    lzfse::compress(bgra)
}
