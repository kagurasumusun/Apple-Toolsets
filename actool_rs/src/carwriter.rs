use crate::bomwriter::BOMWriter;
use crate::csi::build_csi_png;
use byteorder::{BigEndian, ByteOrder, LittleEndian, WriteBytesExt};
use uuid::Uuid;

pub const KEY_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const IOS_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const MAC_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const TV_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];
pub const WATCH_ATTRIBUTES: &[u16] = &[17, 12, 15, 24, 7, 13];

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

pub fn select_key_attributes(platform: &str) -> &'static [u16] {
    match platform {
        "macosx" | "mac" => MAC_ATTRIBUTES,
        "appletvos" | "tvos" => TV_ATTRIBUTES,
        "watchos" | "watch" => WATCH_ATTRIBUTES,
        _ => IOS_ATTRIBUTES,
    }
}

pub struct CARWriter {
    renditions: Vec<AssetRendition>,
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
        identifier: u16,
    ) {
        let filename = format!("{}.png", name);
        let csi_bytes = build_csi_png(bgra, width, height, &filename, scale as u32, true);

        self.add_rendition(AssetRendition {
            name: name.to_string(),
            filename,
            csi_bytes,
            identifier,
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
        identifier: u16,
    ) {
        let mut csi_bytes = vec![0u8; 184];
        csi_bytes[0..4].copy_from_slice(b"ISTC");
        csi_bytes[24..28].copy_from_slice(b"COLR");

        // TLV for color components
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
            identifier,
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

        // 1. CARHEADER Block (436 bytes)
        let mut car_hdr = vec![0u8; 436];
        car_hdr[0..4].copy_from_slice(b"CTAR"); // Big endian magic
        BigEndian::write_u32(&mut car_hdr[4..8], 975); // coreUI version
        BigEndian::write_u32(&mut car_hdr[8..12], 1); // storage version
        BigEndian::write_u32(&mut car_hdr[12..16], 1700000000); // timestamp
        BigEndian::write_u32(&mut car_hdr[16..20], self.renditions.len() as u32);

        let main_ver = b"actool-rs 0.1.0";
        car_hdr[20..20 + main_ver.len()].copy_from_slice(main_ver);
        car_hdr[148..148 + main_ver.len()].copy_from_slice(main_ver);

        let random_uuid = Uuid::new_v4();
        car_hdr[404..420].copy_from_slice(random_uuid.as_bytes());

        BigEndian::write_u32(&mut car_hdr[420..424], 0);
        BigEndian::write_u32(&mut car_hdr[424..428], 1);
        BigEndian::write_u32(&mut car_hdr[428..432], 1); // sRGB
        BigEndian::write_u32(&mut car_hdr[432..436], 1);

        writer.add_block(car_hdr, Some("CARHEADER".to_string()));

        // 2. KEYFORMAT Block
        let attrs = select_key_attributes(&self.platform);
        let mut kfmt = vec![0u8; 12 + attrs.len() * 4];
        kfmt[0..4].copy_from_slice(b"kfmt");
        BigEndian::write_u32(&mut kfmt[4..8], 0);
        BigEndian::write_u32(&mut kfmt[8..12], attrs.len() as u32);
        for (i, &attr) in attrs.iter().enumerate() {
            BigEndian::write_u32(&mut kfmt[12 + i * 4..16 + i * 4], attr as u32);
        }
        writer.add_block(kfmt, Some("KEYFORMAT".to_string()));

        // 3. CSI Rendition payload blocks
        let mut rendition_blocks = Vec::new();
        for r in &self.renditions {
            let block_id = writer.add_block(r.csi_bytes.clone(), None);
            rendition_blocks.push((r, block_id));
        }

        // 4. B-Trees
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
