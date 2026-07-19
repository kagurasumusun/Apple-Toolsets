use crate::lzfse;

pub fn planar_delta_encode(bgra: &[u8], width: u32, height: u32) -> Vec<u8> {
    if bgra.is_empty() {
        return Vec::new();
    }

    let count = (width * height) as usize;
    if bgra.len() < count * 4 {
        return lzfse::compress(bgra);
    }

    // Separate into planes B, G, R, A and delta encode
    let mut delta_buf = vec![0u8; bgra.len()];
    let mut prev_b = 0u8;
    let mut prev_g = 0u8;
    let mut prev_r = 0u8;
    let mut prev_a = 0u8;

    for i in 0..count {
        let b = bgra[i * 4];
        let g = bgra[i * 4 + 1];
        let r = bgra[i * 4 + 2];
        let a = bgra[i * 4 + 3];

        delta_buf[i] = b.wrapping_sub(prev_b);
        delta_buf[count + i] = g.wrapping_sub(prev_g);
        delta_buf[count * 2 + i] = r.wrapping_sub(prev_r);
        delta_buf[count * 3 + i] = a.wrapping_sub(prev_a);

        prev_b = b;
        prev_g = g;
        prev_r = r;
        prev_a = a;
    }

    lzfse::compress(&delta_buf)
}
