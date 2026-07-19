import os
import shutil
import json
from pathlib import Path

reports_dir = Path("wiki/5_research_reports")

categories = {
    "01_atlas_and_packing": ["atlas", "brandassets"],
    "02_compression_cbck": ["cbck", "lzfse", "compress"],
    "03_icon_and_layer_stacks": ["iconstack", "layer-stack", "solidimagestack", "image-stack", "vision", "watch"],
    "04_colors_and_palettes": ["palette", "color"],
    "05_diagnostics_and_corruptions": ["diagnostic", "corrupt"],
    "06_apple_matrix_and_oracles": ["oracle", "xcode", "runtime", "matrix", "option-cross", "source-asset", "template"],
    "07_misc_evidence": []
}

for cat in categories.keys():
    (reports_dir / cat).mkdir(exist_ok=True)

# 1. 隔離環境ですでにフォルダ化されているものを移動
for item in ["oracle-census", "runtime-screenshots-verified"]:
    src = reports_dir / item
    if src.exists():
        shutil.move(str(src), str(reports_dir / "06_apple_matrix_and_oracles" / item))

# 2. ファイルをキーワードベースで分類
for f in os.listdir(reports_dir):
    f_path = reports_dir / f
    if not f_path.is_file():
        continue
    
    moved = False
    for cat, keywords in categories.items():
        if any(kw in f.lower() for kw in keywords):
            shutil.move(str(f_path), str(reports_dir / cat / f))
            moved = True
            break
            
    if not moved and f != "README.md" and f != "INDEX.md":
        shutil.move(str(f_path), str(reports_dir / "07_misc_evidence" / f))

# 3. インデックス作成
index_content = "# 📊 Research Reports & Oracle Matrices\\n\\n"
index_content += "このディレクトリには、Apple純正の `actool` や `assetutil` との完全な挙動比較（数百パターンに及ぶマトリクス検証）、および各種バグや仕様限界の生データ（JSON、ダンプ）が格納されています。\\n\\n"

for cat in sorted(categories.keys()):
    index_content += f"## {cat.replace('_', ' ').title()}\\n"
    cat_dir = reports_dir / cat
    if cat_dir.exists():
        for item in sorted(os.listdir(cat_dir)):
            index_content += f"- `{item}`\\n"
    index_content += "\\n"

with open(reports_dir / "INDEX.md", "w") as f:
    f.write(index_content)
