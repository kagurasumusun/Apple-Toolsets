use crate::carwriter::AssetRendition;
use crate::csi::build_tlv;
use byteorder::{LittleEndian, WriteBytesExt};

pub const ATLAS_PADDING: u32 = 2;

pub fn atlas_name(opaque: bool, gray: bool) -> String {
    format!(
        "ZZZZPackedAsset-1.{}.{}-gamut0",
        if opaque { 1 } else { 0 },
        if gray { 1 } else { 0 }
    )
}

pub fn is_pack_candidate(rendition: &AssetRendition) -> bool {
    rendition.scale == 1
        && rendition.idiom == 0
        && rendition.width > 0
        && rendition.height > 0
        && !rendition.name.starts_with("ZZZZPackedAsset")
}

#[derive(Debug, Clone)]
pub struct ShelfPackRegion {
    pub x: u32,
    pub y: u32,
    pub width: u32,
    pub height: u32,
    pub rendition_index: usize,
}

pub fn shelf_pack(
    items: &[(usize, u32, u32)],
    max_width: u32,
) -> (u32, u32, Vec<ShelfPackRegion>) {
    let mut sorted = items.to_vec();
    sorted.sort_by(|a, b| b.2.cmp(&a.2));

    let mut current_x = ATLAS_PADDING;
    let mut current_y = ATLAS_PADDING;
    let mut shelf_height = 0;
    let mut max_y = 0;
    let mut regions = Vec::new();

    for (idx, w, h) in sorted {
        if current_x + w + ATLAS_PADDING > max_width {
            current_x = ATLAS_PADDING;
            current_y += shelf_height + ATLAS_PADDING;
            shelf_height = 0;
        }

        regions.push(ShelfPackRegion {
            x: current_x,
            y: current_y,
            width: w,
            height: h,
            rendition_index: idx,
        });

        current_x += w + ATLAS_PADDING;
        shelf_height = std::cmp::max(shelf_height, h);
        max_y = std::cmp::max(max_y, current_y + h + ATLAS_PADDING);
    }

    (max_width, max_y, regions)
}

pub fn build_link_tlv(x: u32, y: u32, w: u32, h: u32, page: u16) -> Vec<u8> {
    let mut value = Vec::new();
    value.extend_from_slice(b"INLK");
    let _ = value.write_u16::<LittleEndian>(x as u16);
    let _ = value.write_u16::<LittleEndian>(y as u16);
    let _ = value.write_u16::<LittleEndian>(w as u16);
    let _ = value.write_u16::<LittleEndian>(h as u16);
    let _ = value.write_u16::<LittleEndian>(0);
    let _ = value.write_u16::<LittleEndian>(page);

    build_tlv(1010, &value)
}

pub fn pack_renditions(renditions: Vec<AssetRendition>) -> Vec<AssetRendition> {
    let mut candidates = Vec::new();
    let mut non_candidates = Vec::new();

    for (i, r) in renditions.into_iter().enumerate() {
        if is_pack_candidate(&r) {
            candidates.push((i, r));
        } else {
            non_candidates.push(r);
        }
    }

    if candidates.len() < 2 {
        let mut all = non_candidates;
        for (_, r) in candidates {
            all.push(r);
        }
        return all;
    }

    let pack_items: Vec<(usize, u32, u32)> = candidates
        .iter()
        .enumerate()
        .map(|(idx, (_, r))| (idx, r.width, r.height))
        .collect();

    let (atlas_w, atlas_h, regions) = shelf_pack(&pack_items, 2048);
    let atlas_bgra = vec![0u8; (atlas_w * atlas_h * 4) as usize];

    let mut result_renditions = non_candidates;

    for reg in regions {
        let (_, candidate_rendition) = &candidates[reg.rendition_index];
        let link_tlv = build_link_tlv(reg.x, reg.y, reg.width, reg.height, 0);

        let mut packed_rend = candidate_rendition.clone();
        packed_rend.csi_bytes = link_tlv;
        result_renditions.push(packed_rend);
    }

    let atlas_csi = crate::csi::build_csi_png(
        &atlas_bgra,
        atlas_w,
        atlas_h,
        &atlas_name(true, false),
        1,
        false,
    );

    result_renditions.push(AssetRendition {
        name: atlas_name(true, false),
        filename: format!("{}.png", atlas_name(true, false)),
        csi_bytes: atlas_csi,
        identifier: 0,
        idiom: 0,
        scale: 1,
        gamut: 0,
        appearance: 0,
        width: atlas_w,
        height: atlas_h,
    });

    result_renditions
}
