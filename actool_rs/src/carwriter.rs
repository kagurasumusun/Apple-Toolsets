use crate::bomwriter::BOMWriter;
use crate::csi::build_csi_png;
use byteorder::{BigEndian, ByteOrder, LittleEndian, WriteBytesExt};
use std::collections::HashMap;
use uuid::Uuid;

pub const KEY_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const IOS_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const MAC_ATTRIBUTES: &[u16] = &[17, 12, 1, 2, 3, 17, 8, 11, 12];
pub const TV_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const WATCH_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];

pub fn select_key_attributes(platform: &str) -> &'static [u16] {
    match platform {
        "macosx" | "mac" => MAC_ATTRIBUTES,
        "appletvos" | "tvos" => TV_ATTRIBUTES,
        "watchos" | "watch" => WATCH_ATTRIBUTES,
        _ => IOS_ATTRIBUTES,
    }
}

pub fn fixed(value: f32) -> u32 {
    (value * 65536.0) as u32
}

pub fn identifier(name: &str) -> u16 {
    let poly_hash = crate::facet_hash_lookup::FacetHashLookupTable::compute_polynomial_hash(name);
    (poly_hash % 65536) as u16
}

pub fn localization_identifier(name: &str) -> u16 {
    if name.is_empty() || name == "universal" || name == "Any" {
        0
    } else {
        identifier(name)
    }
}

pub fn car_header(core_ui_version: u32, rendition_count: u32, main_version: &str) -> Vec<u8> {
    let mut car_hdr = vec![0u8; 436];
    car_hdr[0..4].copy_from_slice(b"CTAR");
    BigEndian::write_u32(&mut car_hdr[4..8], core_ui_version);
    BigEndian::write_u32(&mut car_hdr[8..12], 1);
    BigEndian::write_u32(&mut car_hdr[12..16], 1700000000);
    BigEndian::write_u32(&mut car_hdr[16..20], rendition_count);

    let ver_bytes = main_version.as_bytes();
    let len = std::cmp::min(ver_bytes.len(), 127);
    car_hdr[20..20 + len].copy_from_slice(&ver_bytes[..len]);
    car_hdr[148..148 + len].copy_from_slice(&ver_bytes[..len]);

    let random_uuid = Uuid::new_v4();
    car_hdr[404..420].copy_from_slice(random_uuid.as_bytes());

    BigEndian::write_u32(&mut car_hdr[420..424], 0);
    BigEndian::write_u32(&mut car_hdr[424..428], 1);
    BigEndian::write_u32(&mut car_hdr[428..432], 1);
    BigEndian::write_u32(&mut car_hdr[432..436], 1);

    car_hdr
}

pub fn extended_metadata(author: &str, platform: &str, target: &str) -> Vec<u8> {
    let mut meta = vec![0u8; 1028];
    meta[0..4].copy_from_slice(b"META");

    let write_str = |buf: &mut [u8], offset: usize, val: &str| {
        let bytes = val.as_bytes();
        let len = std::cmp::min(bytes.len(), 255);
        buf[offset..offset + len].copy_from_slice(&bytes[..len]);
    };

    write_str(&mut meta, 4, author);
    write_str(&mut meta, 260, target);
    write_str(&mut meta, 516, platform);
    write_str(&mut meta, 772, "actool-rs 0.1.0");

    meta
}

pub fn key_format(attributes: &[u16]) -> Vec<u8> {
    let mut kfmt = vec![0u8; 12 + attributes.len() * 4];
    kfmt[0..4].copy_from_slice(b"kfmt");
    BigEndian::write_u32(&mut kfmt[4..8], 0);
    BigEndian::write_u32(&mut kfmt[8..12], attributes.len() as u32);
    for (i, &attr) in attributes.iter().enumerate() {
        BigEndian::write_u32(&mut kfmt[12 + i * 4..16 + i * 4], attr as u32);
    }
    kfmt
}

pub fn appearance_names_for(renditions: &[AssetRendition]) -> Vec<String> {
    let mut names = Vec::new();
    for r in renditions {
        if r.appearance > 0 {
            let name = format!("Appearance_{}", r.appearance);
            if !names.contains(&name) {
                names.push(name);
            }
        }
    }
    names
}

pub fn appearance_registry(appearances: &[String]) -> HashMap<String, u16> {
    let mut reg = HashMap::new();
    for (i, name) in appearances.iter().enumerate() {
        reg.insert(name.clone(), (i + 1) as u16);
    }
    reg
}

pub fn adapt_csi_for_profile(csi_data: &[u8], profile_dialect: &str) -> Vec<u8> {
    let mut adapted = csi_data.to_vec();
    if profile_dialect == "coreui-918" && adapted.len() >= 184 {
        let _ = (&mut adapted[4..8]).write_u32::<LittleEndian>(918);
    }
    adapted
}

#[derive(Debug, Clone)]
pub struct AssetRendition {
    pub name: String,
    pub filename: String,
    pub csi_bytes: Vec<u8>,
    pub identifier: u16,
    pub idiom: u16,
    pub scale: u16,
    pub gamut: u16,
    pub appearance: u16,
    pub width: u32,
    pub height: u32,
}

pub struct CARWriter {
    pub renditions: Vec<AssetRendition>,
    pub platform: String,
}

impl CARWriter {
    pub fn new(platform: &str) -> Self {
        Self {
            renditions: Vec::new(),
            platform: platform.to_string(),
        }
    }

    pub fn add_rendition(&mut self, rendition: AssetRendition) {
        self.renditions.push(rendition);
    }

    pub fn add_png_image(
        &mut self,
        name: &str,
        bgra: &[u8],
        width: u32,
        height: u32,
        scale: u16,
        idiom: u16,
        ident: u16,
    ) {
        let filename = format!("{}.png", name);
        let csi_bytes = build_csi_png(bgra, width, height, &filename, scale as u32, true);

        self.add_rendition(AssetRendition {
            name: name.to_string(),
            filename,
            csi_bytes,
            identifier: ident,
            idiom,
            scale,
            gamut: 0,
            appearance: 0,
            width,
            height,
        });
    }

    pub fn add_color(
        &mut self,
        name: &str,
        r: f32,
        g: f32,
        b: f32,
        a: f32,
        ident: u16,
    ) {
        let mut csi_bytes = vec![0u8; 184];
        csi_bytes[0..4].copy_from_slice(b"ISTC");
        csi_bytes[24..28].copy_from_slice(b"COLR");

        let mut colr_tlv = Vec::new();
        colr_tlv.extend_from_slice(&r.to_le_bytes());
        colr_tlv.extend_from_slice(&g.to_le_bytes());
        colr_tlv.extend_from_slice(&b.to_le_bytes());
        colr_tlv.extend_from_slice(&a.to_le_bytes());

        let tlv = crate::csi::build_tlv(1008, &colr_tlv);
        let tlv_len = tlv.len() as u32;

        let _ = (&mut csi_bytes[168..172]).write_u32::<LittleEndian>(tlv_len);
        csi_bytes.extend_from_slice(&tlv);

        self.add_rendition(AssetRendition {
            name: name.to_string(),
            filename: format!("{}.color", name),
            csi_bytes,
            identifier: ident,
            idiom: 0,
            scale: 1,
            gamut: 0,
            appearance: 0,
            width: 0,
            height: 0,
        });
    }

    pub fn build(&self) -> Vec<u8> {
        let mut writer = BOMWriter::new();

        let car_hdr = car_header(975, self.renditions.len() as u32, "actool-rs 0.1.0");
        writer.add_block(car_hdr, Some("CARHEADER".to_string()));

        let attrs = select_key_attributes(&self.platform);
        let kfmt = key_format(attrs);
        writer.add_block(kfmt, Some("KEYFORMAT".to_string()));

        let ext_meta = extended_metadata("xcode", &self.platform, "15.0");
        writer.add_block(ext_meta, Some("EXTENDED_METADATA".to_string()));

        let mut rendition_blocks = Vec::new();
        for r in &self.renditions {
            let block_id = writer.add_block(r.csi_bytes.clone(), None);
            rendition_blocks.push((r, block_id));
        }

        let facet_tree = build_btree_block(&[]);
        writer.add_block(facet_tree, Some("FACETKEYS".to_string()));

        let rend_tree = build_btree_block(&rendition_blocks);
        writer.add_block(rend_tree, Some("CAR KEY".to_string()));

        let app_tree = build_btree_block(&[]);
        writer.add_block(app_tree, Some("APPEARANCEKEYS".to_string()));

        let loc_tree = build_btree_block(&[]);
        writer.add_block(loc_tree, Some("LOCALIZATIONKEYS".to_string()));

        writer.build()
    }
}

pub fn build_assets_car(
    renditions: Vec<AssetRendition>,
    platform: &str,
) -> Vec<u8> {
    let mut writer = CARWriter::new(platform);
    for r in renditions {
        writer.add_rendition(r);
    }
    writer.build()
}

fn build_btree_block(items: &[(&AssetRendition, u32)]) -> Vec<u8> {
    let mut buf = Vec::new();

    buf.extend_from_slice(b"BTR3");
    let mut hdr = [0u8; 28];
    BigEndian::write_u32(&mut hdr[0..4], 1);
    BigEndian::write_u32(&mut hdr[4..8], items.len() as u32);
    BigEndian::write_u32(&mut hdr[8..12], 4096);
    buf.extend_from_slice(&hdr);

    for (r, block_id) in items {
        let mut entry = vec![0u8; 16];
        BigEndian::write_u16(&mut entry[0..2], r.identifier);
        BigEndian::write_u16(&mut entry[2..4], r.scale);
        BigEndian::write_u16(&mut entry[4..6], r.idiom);
        BigEndian::write_u16(&mut entry[6..8], r.gamut);
        BigEndian::write_u16(&mut entry[8..10], r.appearance);
        BigEndian::write_u16(&mut entry[10..12], 0);
        BigEndian::write_u32(&mut entry[12..16], *block_id);
        buf.extend_from_slice(&entry);
    }

    buf
}
