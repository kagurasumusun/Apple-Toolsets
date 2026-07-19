use crate::lzfse;

pub fn octree_quantization(bgra: &[u8], max_colors: usize) -> Vec<u8> {
    let step = (256 / std::cmp::max(1, (max_colors as f32).powf(0.25) as usize)) as u8;
    let mut out = bgra.to_vec();
    for px in out.chunks_exact_mut(4) {
        px[0] = (px[0] / step) * step;
        px[1] = (px[1] / step) * step;
        px[2] = (px[2] / step) * step;
    }
    out
}

pub fn wu_quantization(bgra: &[u8], max_colors: usize) -> Vec<u8> {
    octree_quantization(bgra, max_colors)
}

pub struct TETFullCompressor;

impl Default for TETFullCompressor {
    fn default() -> Self {
        Self::new()
    }
}

impl TETFullCompressor {
    pub fn new() -> Self {
        Self
    }

    pub fn compress(&self, bgra: &[u8]) -> Vec<u8> {
        lzfse::compress(bgra)
    }
}

pub fn tet_full_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    let comp = TETFullCompressor::default();
    comp.compress(bgra)
}
