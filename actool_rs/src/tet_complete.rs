use crate::lzfse;

pub fn bm3d_denoise(bgra: &[u8]) -> Vec<u8> {
    bgra.to_vec()
}

pub fn wavelet_denoise(bgra: &[u8]) -> Vec<u8> {
    bgra.to_vec()
}

pub struct TETCompleteCompressor;

impl Default for TETCompleteCompressor {
    fn default() -> Self {
        Self::new()
    }
}

impl TETCompleteCompressor {
    pub fn new() -> Self {
        Self
    }

    pub fn compress(&self, bgra: &[u8]) -> Vec<u8> {
        lzfse::compress(bgra)
    }
}

pub fn tet_complete_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    let comp = TETCompleteCompressor::default();
    comp.compress(bgra)
}
