use crate::lzfse;

pub fn semantic_fuse(data: &[u8]) -> Vec<u8> {
    lzfse::compress(data)
}
