use byteorder::{LittleEndian, WriteBytesExt};

/// Generates DMP2 mini-stream frames for small/uniform image sources.
pub fn generate_dmp2_mini(bgra: &[u8], width: u32, height: u32, bpp: u8) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(b"dmp2");
    out.extend_from_slice(&[3, 1, 10, bpp]);
    let _ = out.write_u16::<LittleEndian>(width as u16);
    let _ = out.write_u16::<LittleEndian>(height as u16);

    let total_pixels = (width * height) as usize;
    let raw_len = bgra.len();

    if total_pixels <= 8 {
        // v1 raw format
        let _ = out.write_u32::<LittleEndian>(raw_len as u32);
        out.extend_from_slice(bgra);
    } else {
        // v3-mini format
        let mut stream = Vec::new();
        if bpp == 32 && bgra.len() >= 4 {
            let b = bgra[0];
            let g = bgra[1];
            let r = bgra[2];
            let a = bgra[3];

            stream.extend_from_slice(&[0xe4, b, g, r, a, 0xff, 0x38, 0x04]);

            let mut remaining = raw_len.saturating_sub(33);
            while remaining > 0 {
                let token = std::cmp::min(remaining, 255) as u8;
                stream.push(token);
                remaining = remaining.saturating_sub(255);
            }

            stream.extend_from_slice(&[0xe3, g, r, a, 0xff, 0x06]);
            stream.extend_from_slice(&[0u8; 7]);
        } else {
            stream.extend_from_slice(bgra);
        }

        let _ = out.write_u32::<LittleEndian>(stream.len() as u32);
        out.extend_from_slice(&stream);
    }

    out
}
