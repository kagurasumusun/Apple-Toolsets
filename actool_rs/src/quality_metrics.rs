pub fn compute_psnr(orig: &[u8], comp: &[u8]) -> f64 {
    if orig.len() != comp.len() || orig.is_empty() {
        return 0.0;
    }

    let mut mse = 0.0f64;
    for (a, b) in orig.iter().zip(comp.iter()) {
        let diff = (*a as f64) - (*b as f64);
        mse += diff * diff;
    }
    mse /= orig.len() as f64;

    if mse < 1e-10 {
        return 99.0;
    }

    10.0 * (255.0 * 255.0 / mse).log10()
}
