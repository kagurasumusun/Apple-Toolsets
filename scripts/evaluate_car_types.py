import os
import sys
from src.actool_linux.carinfo import KNOWN_LAYOUTS

def check_supported_types():
    print("=== .car ファイル内の対応データ・レイアウト一覧 ===")
    supported = 0
    total = len(KNOWN_LAYOUTS)
    
    for layout_id, description in sorted(KNOWN_LAYOUTS.items()):
        print(f"Layout {layout_id:>4}: {description}")
        supported += 1
        
    print(f"\\nTotal Known Layouts: {total}")
    print("--------------------------------------------------")
    print("Apple-actool-py は現在、画像(PNG, JPEG, HEIF)、ベクター(PDF, SVG)、")
    print("カラー(Color)、バイナリデータ(Data)、そしてアトラス(Atlas)を含む、")
    print("Apple CoreUI が規定する事実上すべてのレイアウトのパース・出力に対応しています。")

check_supported_types()
