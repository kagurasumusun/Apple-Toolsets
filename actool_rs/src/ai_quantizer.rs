pub fn quantize_palette(bgra: &[u8], max_colors: usize) -> (Vec<[u8; 4]>, Vec<u8>) {
    let mut palette = Vec::new();
    let mut indices = Vec::new();

    for chunk in bgra.chunks_exact(4) {
        let color = [chunk[0], chunk[1], chunk[2], chunk[3]];
        if let Some(pos) = palette.iter().position(|&c| c == color) {
            indices.push(pos as u8);
        } else if palette.len() < max_colors {
            palette.push(color);
            indices.push((palette.len() - 1) as u8);
        } else {
            indices.push(0);
        }
    }

    (palette, indices)
}
