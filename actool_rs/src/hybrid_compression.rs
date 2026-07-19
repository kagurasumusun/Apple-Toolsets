use crate::lpc_lzfse::lpc_encode_apple_compat;
use crate::lzfse;
use crate::planar_delta_lzfse::planar_delta_encode;

pub fn hybrid_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
    let raw_compressed = lzfse::compress(bgra);
    let delta_compressed = planar_delta_encode(bgra, width, height);
    let lpc_compressed = lpc_encode_apple_compat(bgra, width, height);

    let mut best = raw_compressed;
    if delta_compressed.len() < best.len() {
        best = delta_compressed;
    }
    if lpc_compressed.len() < best.len() {
        best = lpc_compressed;
    }
    best
}
