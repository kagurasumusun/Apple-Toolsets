use actool_rs::appicons::{app_icon_entry_rank, AppIconEntry};
use actool_rs::autosafe::{auto_safe_compress, AlphaCharacteristic, ImageDomain, SafetyLevel};
use actool_rs::bom::BOMStore;
use actool_rs::bomwriter::BOMWriter;
use actool_rs::car::CARFile;
use actool_rs::carwriter::CARWriter;
use actool_rs::cbck::{encode_cbck, parse_cbck};
use actool_rs::compiler::{compile_catalogs, CompileOptions};
use actool_rs::dmp2mini::{decode_mini, v3_mini_color};
use actool_rs::facet_hash_lookup::FacetHashLookupTable;
use actool_rs::hybrid_compression::HybridCompressor;
use actool_rs::lzfse;
use actool_rs::media::{calculate_shannon_entropy, detect_media_type, select_optimal_compression, MediaType};
use actool_rs::model3d::{compress_normal_map_2channel, generate_mipmap_chain, PBRMaterialMap};
use actool_rs::packed::{atlas_name, build_link_tlv};
use actool_rs::planar_delta_lzfse::{delta_decode_plane, delta_encode_plane, planar_delta_decode, planar_delta_encode};
use actool_rs::quality_metrics::{compute_delta_e, compute_psnr, compute_ssim};
use actool_rs::ultrahd::{classify_resolution_tier, encode_ultrahd_tiled_cbck, UltraHDTier};
use std::fs;
use tempfile::tempdir;

#[test]
fn test_bom_roundtrip() {
    let mut writer = BOMWriter::new();
    let id1 = writer.add_block(b"Hello Block 1".to_vec(), Some("CARHEADER".to_string()));
    let id2 = writer.add_block(b"Hello Block 2".to_vec(), Some("KEYFORMAT".to_string()));

    let bytes = writer.build();
    let store = BOMStore::from_bytes(bytes).expect("BOMStore parse failed");

    assert_eq!(store.block_data(id1).unwrap(), b"Hello Block 1");
    assert_eq!(store.block_data(id2).unwrap(), b"Hello Block 2");
    assert_eq!(store.named_block_data("CARHEADER").unwrap(), b"Hello Block 1");
    assert_eq!(store.named_block_data("KEYFORMAT").unwrap(), b"Hello Block 2");
}

#[test]
fn test_lzfse_roundtrip() {
    let original = vec![0xABu8; 10000];
    let compressed = lzfse::compress(&original);
    let decompressed = lzfse::decompress(&compressed).expect("Decompression failed");
    assert_eq!(original, decompressed);
}

#[test]
fn test_cbck_roundtrip() {
    let w = 64u32;
    let h = 64u32;
    let bgra = vec![128u8; (w * h * 4) as usize];

    let payload = encode_cbck(&bgra, w, h, 4, true);
    let parsed = parse_cbck(&payload).expect("CBCK parse failed");

    assert_eq!(parsed.mode, 3);
    assert_eq!(parsed.codec, 4);
    assert!(!parsed.chunks.is_empty());
}

#[test]
fn test_csi_and_car_writer() {
    let mut car_writer = CARWriter::new("iphoneos");
    let bgra = vec![255u8; 32 * 32 * 4];

    car_writer.add_png_image("AppIcon", &bgra, 32, 32, 2, 1, 1);
    let car_bytes = car_writer.build();

    let store = BOMStore::from_bytes(car_bytes).expect("BOMStore parse failed");
    let car = CARFile::from_bom_store(&store).expect("CARFile parse failed");

    assert_eq!(car.header.byte_order, "big");
    assert_eq!(car.header.core_ui_version, 975);
    assert_eq!(car.header.rendition_count, 1);
}

#[test]
fn test_appicon_ranking() {
    let entry = AppIconEntry {
        idiom: Some("iphone".to_string()),
        size: Some("60x60".to_string()),
        scale: Some("2x".to_string()),
        filename: Some("icon60x60@2x.png".to_string()),
        platform: Some("iphoneos".to_string()),
    };

    let result = app_icon_entry_rank(&entry, "iphoneos");
    assert!(result.is_some());
    let (score, w, h) = result.unwrap();
    assert!(score > 0);
    assert_eq!(w, 120);
    assert_eq!(h, 120);
}

#[test]
fn test_compiler_flow() {
    let dir = tempdir().unwrap();
    let cat_dir = dir.path().join("App.xcassets");
    let icon_dir = cat_dir.join("AppIcon.appiconset");
    fs::create_dir_all(&icon_dir).unwrap();

    let contents_json = r#"{
      "images": [
        {"filename": "icon.png", "idiom": "iphone", "scale": "2x", "size": "60x60"}
      ],
      "info": {"author": "xcode", "version": 1}
    }"#;

    fs::write(icon_dir.join("Contents.json"), contents_json).unwrap();

    let img = image::RgbaImage::from_pixel(120, 120, image::Rgba([255, 0, 0, 255]));
    img.save(icon_dir.join("icon.png")).unwrap();

    let out_dir = dir.path().join("out");

    let options = CompileOptions {
        inputs: vec![cat_dir],
        output_dir: out_dir.clone(),
        platform: "iphoneos".to_string(),
        minimum_deployment_target: "15.0".to_string(),
        app_icon: None,
        optimize: Some("smart".to_string()),
        export_dependency_info: None,
        output_format: "human".to_string(),
    };

    let result = compile_catalogs(options).expect("Compilation failed");
    assert!(!result.output_files.is_empty());

    let car_path = out_dir.join("Assets.car");
    assert!(car_path.is_file());

    let store = BOMStore::from_path(&car_path).expect("Read Assets.car failed");
    assert!(store.variables.contains_key("CARHEADER"));
}

#[test]
fn test_dmp2mini_roundtrip() {
    let bgra = [10u8, 20u8, 30u8, 255u8];
    let dmp2 = v3_mini_color(4, 4, &bgra);
    let decoded = decode_mini(&dmp2, 4, 4, 4).expect("Decode dmp2 mini failed");

    assert_eq!(decoded.len(), 4 * 4 * 4);
    assert_eq!(&decoded[0..4], &bgra);
}

#[test]
fn test_facet_hash() {
    let hash = FacetHashLookupTable::compute_polynomial_hash("AppIcon");
    assert!(hash > 0);
}

#[test]
fn test_planar_delta_roundtrip() {
    let plane = vec![10u8, 12u8, 15u8, 20u8, 20u8, 25u8];
    let delta = delta_encode_plane(&plane);
    let decoded = delta_decode_plane(&delta);
    assert_eq!(plane, decoded);

    let bgra = vec![100u8; 16 * 4];
    let encoded = planar_delta_encode(&bgra, 4, 4);
    let decoded_bgra = planar_delta_decode(&encoded).expect("Planar delta decode failed");
    assert_eq!(bgra, decoded_bgra);
}

#[test]
fn test_quality_metrics() {
    let orig = vec![100u8; 300];
    let comp = vec![100u8; 300];

    let psnr = compute_psnr(&orig, &comp);
    assert!(psnr > 90.0);

    let delta_e = compute_delta_e(&orig, &comp);
    assert_eq!(delta_e, 0.0);

    let ssim = compute_ssim(&orig, &comp);
    assert!((ssim - 1.0).abs() < 1e-4);
}

#[test]
fn test_packed_helpers() {
    assert_eq!(atlas_name(true, false), "ZZZZPackedAsset-1.1.0-gamut0");
    let link = build_link_tlv(10, 20, 100, 100, 0);
    assert!(link.len() > 10);
}

#[test]
fn test_hybrid_compressor() {
    let compressor = HybridCompressor::default();
    let bgra = vec![200u8; 16 * 16 * 4];
    let compressed = compressor.compress_chunk(&bgra, 16, 16);
    assert!(!compressed.is_empty());
}

#[test]
fn test_3d_pbr_orm_and_normal_map() {
    let pbr = PBRMaterialMap::new("MetalGold", 32, 32);
    let orm_payload = pbr.compress_orm_payload();
    assert!(!orm_payload.is_empty());

    let rgb_normal = vec![128u8; 32 * 32 * 3];
    let compressed_normal = compress_normal_map_2channel(&rgb_normal, 32, 32);
    assert!(!compressed_normal.is_empty());

    let bgra = vec![200u8; 32 * 32 * 4];
    let mips = generate_mipmap_chain(&bgra, 32, 32);
    assert!(mips.len() >= 5);
    assert_eq!(mips[0].0, 32);
    assert_eq!(mips[1].0, 16);
    assert_eq!(mips[2].0, 8);
}

#[test]
fn test_ar_resource_group() {
    use actool_rs::arresource::{ARReferenceImageSpec, ARResourceGroup};

    let mut group = ARResourceGroup::new("ARObjects");
    group.add_image(ARReferenceImageSpec {
        name: "Poster.jpg".to_string(),
        physical_width_meters: 0.5,
        physical_height_meters: 0.75,
    });

    let json_str = group.serialize_ar_group();
    assert!(json_str.contains("Poster.jpg"));
    assert!(json_str.contains("0.5"));
}

#[test]
fn test_media_type_detection_and_compression() {
    let audio_mp3 = vec![0xFFu8; 1000];
    assert_eq!(detect_media_type("song.mp3", &audio_mp3), MediaType::AudioCompressed);
    let (comp_audio, strat_audio) = select_optimal_compression("song.mp3", &audio_mp3, 0, 0);
    assert_eq!(strat_audio, "raw_passthrough");
    assert_eq!(comp_audio.len(), audio_mp3.len());

    let pdf_bytes = b"%PDF-1.5 test pdf data with vector paths and text objects";
    assert_eq!(detect_media_type("doc.pdf", pdf_bytes), MediaType::Pdf);
    let (comp_pdf, strat_pdf) = select_optimal_compression("doc.pdf", pdf_bytes, 0, 0);
    assert_eq!(strat_pdf, "lzfse_vector_mesh");
    assert!(!comp_pdf.is_empty());

    let model3d = b"v 0.0 0.0 0.0\nv 1.0 1.0 1.0\nf 1 2 3";
    assert_eq!(detect_media_type("mesh.obj", model3d), MediaType::Model3D);

    let low_entropy = vec![0u8; 1000];
    let high_entropy: Vec<u8> = (0..1000).map(|i| (i * 37 % 256) as u8).collect();

    let e_low = calculate_shannon_entropy(&low_entropy);
    let e_high = calculate_shannon_entropy(&high_entropy);

    assert!(e_low < 1.0);
    assert!(e_high > 7.0);
}

#[test]
fn test_ultrahd_tiled_encoding() {
    assert_eq!(classify_resolution_tier(1024, 768), UltraHDTier::Standard);
    assert_eq!(classify_resolution_tier(3840, 2160), UltraHDTier::Resolution4K);
    assert_eq!(classify_resolution_tier(7680, 4320), UltraHDTier::Resolution8K);
    assert_eq!(classify_resolution_tier(15360, 8640), UltraHDTier::Resolution16K);

    let w = 4000u32;
    let h = 2200u32;
    let bgra = vec![128u8; (w * h * 4) as usize];

    let payload = encode_ultrahd_tiled_cbck(&bgra, w, h, 512, true);
    assert!(payload.starts_with(b"MLEC"));
}

#[test]
fn test_auto_safe_optimization_precision_domain() {
    let mut dirty_bgra = vec![0u8; 16 * 4];
    for px in dirty_bgra.chunks_exact_mut(4) {
        px[0] = 100;
        px[1] = 200;
        px[2] = 50;
        px[3] = 0;
    }

    // CustomShaderSafe -> Must preserve dirty alpha
    let (_comp, report) = auto_safe_compress(&dirty_bgra, 2, 2, "texture", SafetyLevel::CustomShaderSafe);
    assert_eq!(report.alpha_type, AlphaCharacteristic::DirtyAlpha);
    assert!(report.is_lossless);

    // Standard UI Image -> Safety check detects dirty alpha and applies clean alpha
    let (_comp2, report2) = auto_safe_compress(&dirty_bgra, 2, 2, "image", SafetyLevel::PerceptualSafe);
    assert_eq!(report2.alpha_type, AlphaCharacteristic::DirtyAlpha);

    // Monochrome image -> Lossless GA8 Normalization
    let mono_bgra = vec![128u8; 16 * 4];
    let (_comp3, report3) = auto_safe_compress(&mono_bgra, 2, 2, "image", SafetyLevel::AutoDomainDetect);
    assert_eq!(report3.detected_domain, ImageDomain::GrayscaleUI);
    assert!(report3.is_monochrome);
}

#[test]
fn test_native_gpu_direct_astc_blocks() {
    use actool_rs::astc_native::{build_astc_gpu_direct_csi, ASTCGPUDirectBlockDim};

    let bgra = vec![128u8; 16 * 16 * 4];
    let csi_4x4 = build_astc_gpu_direct_csi(&bgra, 16, 16, "texture_astc.png", ASTCGPUDirectBlockDim::Block4x4);
    assert!(csi_4x4.len() > 184);
    assert_eq!(&csi_4x4[24..28], b"AS44");

    let csi_8x8 = build_astc_gpu_direct_csi(&bgra, 16, 16, "texture_astc.png", ASTCGPUDirectBlockDim::Block8x8);
    assert_eq!(&csi_8x8[24..28], b"AS88");
}

#[test]
fn test_audio_optimization_and_snr_quality_gate() {
    use actool_rs::audio::{compute_signal_to_noise_ratio_db, optimize_audio_payload};

    let signal = vec![1000i16; 100];
    let identical = vec![1000i16; 100];
    let snr = compute_signal_to_noise_ratio_db(&signal, &identical);
    assert!(snr > 100.0);

    let pcm = vec![100u8; 2000];
    let (comp, report) = optimize_audio_payload("sample.wav", &pcm, 60.0);
    assert!(report.is_lossless);
    assert!(report.snr_db >= 60.0);
    assert!(!comp.is_empty());
}

#[test]
fn test_human_ergonomics_and_ciede2000_jnd() {
    use actool_rs::ciede2000::compute_ciede2000;
    use actool_rs::ergonomics::evaluate_human_visual_ergonomics;
    use actool_rs::psychoacoustics::evaluate_human_auditory_safety;

    // Test CIEDE2000 identical color -> Delta E00 = 0.0
    let lab1 = (50.0, 10.0, -20.0);
    let lab2 = (50.0, 10.0, -20.0);
    let de00 = compute_ciede2000(lab1, lab2);
    assert_eq!(de00, 0.0);

    // Test CIEDE2000 JND threshold on image
    let orig_bgra = vec![128u8; 16 * 4];
    let comp_bgra = vec![128u8; 16 * 4];
    let ergo_report = evaluate_human_visual_ergonomics(&orig_bgra, &comp_bgra, 2, 2);
    assert!(ergo_report.is_imperceptible_to_all_humans);
    assert_eq!(ergo_report.delta_e_00, 0.0);
    assert_eq!(ergo_report.jnd_status, "PERFECT_HUMAN_IMPERCEPTIBLE_JND");

    // Test Psychoacoustics 80dB SNR threshold
    let pcm_orig = vec![1000i16; 100];
    let pcm_comp = vec![1000i16; 100];
    let (audio_safe, snr_db) = evaluate_human_auditory_safety(&pcm_orig, &pcm_comp);
    assert!(audio_safe);
    assert!(snr_db >= 80.0);
}

#[test]
fn test_repair_corrupted_car_archive() {
    use actool_rs::repair::repair_corrupted_car;

    // Create a valid CSI rendition and prepended corrupted garbage magic
    let bgra = vec![255u8; 16 * 16 * 4];
    let csi_valid = actool_rs::csi::build_csi_png(&bgra, 16, 16, "IconCorrupted", 1, true);

    let mut corrupted_bytes = b"CORRUPTED_MAGIC_HEADER_GARBAGE_BYTES_123456789".to_vec();
    corrupted_bytes.extend_from_slice(&csi_valid);

    let (repaired, report) = repair_corrupted_car(&corrupted_bytes).expect("Repair failed");
    assert!(report.magic_repaired);
    assert!(report.recovered_renditions >= 1);
    assert!(!repaired.is_empty());

    // Parse repaired buffer to confirm valid BOMStore and CARFile
    let store = BOMStore::from_bytes(repaired).expect("Repaired BOM parse failed");
    assert!(store.variables.contains_key("CARHEADER"));
}

#[test]
fn test_car_editor_and_virtual_storage_mount() {
    use actool_rs::editor::CAREditor;
    use actool_rs::mount::{mount_car_to_directory, sync_directory_to_car};

    let dir = tempdir().unwrap();
    let initial_car_path = dir.path().join("InitialAssets.car");

    // Build initial Assets.car using CARWriter
    let mut writer = CARWriter::new("iphoneos");
    let bgra = vec![200u8; 16 * 16 * 4];
    writer.add_png_image("HomeIcon", &bgra, 16, 16, 1, 0, 1);
    fs::write(&initial_car_path, writer.build()).unwrap();

    // 1. Load in CAREditor, add new asset, replace asset, remove asset
    let mut editor = CAREditor::load(&initial_car_path).expect("Load editor failed");
    let new_bgra = vec![100u8; 32 * 32 * 4];
    editor.add_or_replace_image("ProfileIcon", &new_bgra, 32, 32);
    assert!(editor.renditions.contains_key("ProfileIcon"));

    let edited_car_path = dir.path().join("EditedAssets.car");
    editor.save(&edited_car_path).expect("Save edited CAR failed");
    assert!(edited_car_path.is_file());

    // 2. Mount CAR as virtual storage directory
    let mount_dir = dir.path().join("mounted_storage");
    let count = mount_car_to_directory(&edited_car_path, &mount_dir).expect("Mount failed");
    assert!(count >= 1);
    assert!(mount_dir.join("mount_manifest.json").is_file());

    // 3. Edit files inside mounted directory and sync back to new CAR
    let new_png_path = mount_dir.join("NewAddFromStorage.png");
    fs::write(&new_png_path, vec![128u8; 16 * 16 * 4]).unwrap();

    let synced_car_path = dir.path().join("SyncedAssets.car");
    sync_directory_to_car(&mount_dir, &synced_car_path).expect("Sync from mount failed");
    assert!(synced_car_path.is_file());

    let final_store = BOMStore::from_path(&synced_car_path).expect("Final store read failed");
    assert!(final_store.variables.contains_key("CARHEADER"));
}

#[test]
fn test_non_image_advanced_optimizations() {
    use actool_rs::nonimage_optimizer::{
        optimize_3d_mesh_geometry, optimize_json_lottie, optimize_non_image_asset,
        optimize_pcm_audio_advanced,
    };

    // 1. JSON / Lottie Motion Curve Optimization
    let lottie_json = br#"{
        "v": "5.7.4",
        "fr": 60,
        "ip": 0.000000000,
        "op": 180.123456789,
        "w": 512,
        "h": 512
    }"#;
    let res_json = optimize_json_lottie(lottie_json);
    assert!(res_json.optimized_bytes < res_json.original_bytes);
    assert_eq!(res_json.asset_category, "JSON/Lottie");

    // 2. PCM Audio Silence Trimming & Delta LPC Encoding
    let mut pcm = vec![1000i16.to_le_bytes()[0], 1000i16.to_le_bytes()[1]];
    for _ in 0..500 {
        pcm.push(500i16.to_le_bytes()[0]);
        pcm.push(500i16.to_le_bytes()[1]);
    }
    // Append 200 bytes of silence (0) at the end
    pcm.extend_from_slice(&[0u8; 200]);

    let res_audio = optimize_pcm_audio_advanced(&pcm);
    assert_eq!(res_audio.asset_category, "Audio");
    assert!(res_audio.optimized_bytes < res_audio.original_bytes);

    // 3. 3D Mesh OBJ Geometry Vertex Quantization
    let mesh_obj = b"v 1.23456789 2.34567890 3.45678901\nv -0.98765432 -1.87654321 0.00000000\n";
    let res_mesh = optimize_3d_mesh_geometry(mesh_obj);
    assert_eq!(res_mesh.asset_category, "3D Mesh");
    assert!(res_mesh.optimized_bytes < res_mesh.original_bytes);

    // 4. Universal Non-Image Router
    let res_auto = optimize_non_image_asset("animation.json", lottie_json);
    assert_eq!(res_auto.asset_category, "JSON/Lottie");
}
