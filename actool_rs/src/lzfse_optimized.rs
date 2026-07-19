use crate::lzfse;

pub fn compress_optimized(data: &[u8]) -> Vec<u8> {
    lzfse::compress(data)
}
