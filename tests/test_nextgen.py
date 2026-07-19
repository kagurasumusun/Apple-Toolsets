from actool_linux.nextgen.smart_cbck import SmartCBCKEncoder
import numpy as np

# 1. 128x128 のダミー画像を生成 (透明領域と、少しのUIパーツ)
data = np.zeros((128, 128, 4), dtype=np.uint8)
data[10:30, 10:30] = [255, 0, 0, 255] # 赤い四角 (UI)
data[60:100, 60:100] = [0, 255, 0, 255] # 緑の四角 (UI)

# 2. エンコーダを初期化してエンコード
encoder = SmartCBCKEncoder(clean_alpha=True, max_chunk_size=128)
try:
    encoded = encoder.encode(data.tobytes(), 128, 128)
    print(f"Success! Encoded payload size: {len(encoded)} bytes")
except Exception as e:
    print(f"Error: {e}")
