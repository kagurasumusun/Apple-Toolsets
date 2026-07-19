use crate::lzfse;

pub fn dmp2_rle_optimize(raw: &[u8], _bpp: u8) -> Vec<u8> {
    lzfse::compress(raw)
}

pub fn optimize_dmp2_payload(raw: &[u8], bpp: u8) -> Vec<u8> {
    dmp2_rle_optimize(raw, bpp)
}
