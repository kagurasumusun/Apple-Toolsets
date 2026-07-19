use crate::lzfse;

pub fn optimize_dmp2_payload(raw: &[u8], _bpp: u8) -> Vec<u8> {
    lzfse::compress(raw)
}
