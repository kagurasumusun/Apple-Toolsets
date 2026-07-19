pub fn compute_variant_delta(light: &[u8], dark: &[u8]) -> (Vec<i16>, f64) {
    let min_len = std::cmp::min(light.len(), dark.len());
    let mut delta = Vec::with_capacity(min_len);
    let mut identical_count = 0;

    for i in 0..min_len {
        let diff = (dark[i] as i16) - (light[i] as i16);
        if diff == 0 {
            identical_count += 1;
        }
        delta.push(diff);
    }

    let ratio = (identical_count as f64) / (min_len.max(1) as f64);
    (delta, ratio)
}

pub fn tet_variant_compress(bgra: &[u8], _width: u32, _height: u32) -> Vec<u8> {
    crate::lzfse::compress(bgra)
}
