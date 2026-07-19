use thiserror::Error;

#[derive(Error, Debug)]
pub enum PaletteImageError {
    #[error("Theme pixel rendition is truncated")]
    Truncated,
    #[error("Invalid theme pixel rendition magic")]
    InvalidMagic,
    #[error("Palette color count out of range: {0}")]
    OutOfRange(usize),
}

#[derive(Debug, Clone)]
pub struct ThemePixelRendition {
    pub version: u32,
    pub compression_type: u32,
    pub raw_data: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct QuantizedImageData {
    pub version: u32,
    pub palette: Vec<[u8; 4]>,
    pub indices: Vec<u8>,
    pub bits_per_index: usize,
}

pub fn bit_width(palette_count: usize) -> Result<usize, PaletteImageError> {
    if !(1..=4096).contains(&palette_count) {
        return Err(PaletteImageError::OutOfRange(palette_count));
    }
    for bits in [1, 2, 4, 8] {
        if palette_count <= (1 << bits) {
            return Ok(bits);
        }
    }
    Ok(12)
}

pub fn parse_theme_pixel_rendition(data: &[u8]) -> Result<ThemePixelRendition, PaletteImageError> {
    if data.len() < 16 {
        return Err(PaletteImageError::Truncated);
    }

    let magic = &data[0..4];
    if magic != b"MLEC" && magic != b"CELM" {
        return Err(PaletteImageError::InvalidMagic);
    }

    let is_little = magic == b"MLEC";

    let version = if is_little {
        u32::from_le_bytes(data[4..8].try_into().unwrap())
    } else {
        u32::from_be_bytes(data[4..8].try_into().unwrap())
    };

    let compression_type = if is_little {
        u32::from_le_bytes(data[8..12].try_into().unwrap())
    } else {
        u32::from_be_bytes(data[8..12].try_into().unwrap())
    };

    let raw_data = data[16..].to_vec();

    Ok(ThemePixelRendition {
        version,
        compression_type,
        raw_data,
    })
}
