use crate::editor::CAREditor;
use std::fs;
use std::path::Path;

/// Virtual Storage Mounting & Extraction/Sync Engine
/// Mounts a CAR archive as a virtual filesystem directory tree for interactive editing.
pub fn mount_car_to_directory<P: AsRef<Path>>(car_path: P, mount_dir: P) -> Result<usize, String> {
    let editor = CAREditor::load(&car_path)?;
    fs::create_dir_all(&mount_dir).map_err(|e| e.to_string())?;

    let mut extracted_count = 0;
    for (name, rend) in &editor.renditions {
        let file_path = mount_dir.as_ref().join(format!("{}.png", name));
        let _ = fs::write(file_path, &rend.csi_bytes);
        extracted_count += 1;
    }

    // Write a manifest metadata JSON in the mount storage root
    let manifest_path = mount_dir.as_ref().join("mount_manifest.json");
    let _ = fs::write(
        manifest_path,
        serde_json::json!({
            "mounted_car": car_path.as_ref().display().to_string(),
            "asset_count": extracted_count,
            "read_write_enabled": true
        })
        .to_string(),
    );

    Ok(extracted_count)
}

/// Syncs edited virtual directory files back into a clean Assets.car archive
pub fn sync_directory_to_car<P: AsRef<Path>>(mount_dir: P, output_car_path: P) -> Result<(), String> {
    let mut editor = CAREditor::new("iphoneos");

    let entries = fs::read_dir(&mount_dir).map_err(|e| e.to_string())?;
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("png") {
            let stem = path.file_stem().unwrap_or_default().to_string_lossy();
            if let Ok(bytes) = fs::read(&path) {
                editor.add_or_replace_image(&stem, &bytes, 100, 100);
            }
        }
    }

    editor.save(output_car_path)
}
