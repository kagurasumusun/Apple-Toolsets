use crate::lzfse;

pub fn compress(data: &[u8]) -> Vec<u8> {
    lzfse::compress(data)
}

pub fn decompress(data: &[u8]) -> Result<Vec<u8>, &'static str> {
    lzfse::decompress(data)
}
