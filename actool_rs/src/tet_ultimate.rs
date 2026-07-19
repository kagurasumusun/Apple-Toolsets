use crate::lzfse;

pub fn left_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8> {
    if bgra.len() < width * height * 4 {
        return bgra.to_vec();
    }
    let mut out = vec![0u8; bgra.len()];

    for y in 0..height {
        for x in 0..width {
            let idx = (y * width + x) * 4;
            if x == 0 {
                out[idx..idx + 4].copy_from_slice(&bgra[idx..idx + 4]);
            } else {
                let prev_idx = (y * width + (x - 1)) * 4;
                out[idx] = bgra[idx].wrapping_sub(bgra[prev_idx]);
                out[idx + 1] = bgra[idx + 1].wrapping_sub(bgra[prev_idx + 1]);
                out[idx + 2] = bgra[idx + 2].wrapping_sub(bgra[prev_idx + 2]);
                out[idx + 3] = bgra[idx + 3].wrapping_sub(bgra[prev_idx + 3]);
            }
        }
    }

    out
}

pub fn top_predictor(bgra: &[u8], width: usize, height: usize) -> Vec<u8> {
    if bgra.len() < width * height * 4 {
        return bgra.to_vec();
    }
    let mut out = vec![0u8; bgra.len()];

    for y in 0..height {
        for x in 0..width {
            let idx = (y * width + x) * 4;
            if y == 0 {
                out[idx..idx + 4].copy_from_slice(&bgra[idx..idx + 4]);
            } else {
                let prev_idx = ((y - 1) * width + x) * 4;
                out[idx] = bgra[idx].wrapping_sub(bgra[prev_idx]);
                out[idx + 1] = bgra[idx + 1].wrapping_sub(bgra[prev_idx + 1]);
                out[idx + 2] = bgra[idx + 2].wrapping_sub(bgra[prev_idx + 2]);
                out[idx + 3] = bgra[idx + 3].wrapping_sub(bgra[prev_idx + 3]);
            }
        }
    }

    out
}

pub fn tet_ultimate_compress(bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
    let predicted = left_predictor(bgra, width as usize, height as usize);
    lzfse::compress(&predicted)
}
