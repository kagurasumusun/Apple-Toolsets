from __future__ import annotations
import struct
import numpy as np

try:
    from actool_linux.stable import lzfse_compat as lzfse
except ImportError:
    try:
        import lzfse
    except ImportError:
        lzfse = None

# AppleのDMP2/CBCKフォーマットの定数
DMP2_CBCK_CHUNK_RAW_CAP = 16384 # 16KB

class SmartCBCKEncoder:
    """
    新世代の超高効率CBCKエンコーダ (QuadTree + RLE + LZFSE/Raw Fallback)。
    
    Appleのフォーマット (KCBC マジック) に完全に準拠しつつ、内部のチャンク分割と
    圧縮アルゴリズムの選択を極限まで最適化します。
    """
    def __init__(self, clean_alpha: bool = True, max_chunk_size: int = 128):
        self.clean_alpha = clean_alpha # Dirty Transparencyの消去フラグ
        self.max_chunk_size = max_chunk_size # Apple互換性を保つ最大サイズ (128x128など)
        
    def _clean_dirty_transparency(self, img_np: np.ndarray) -> np.ndarray:
        """Alpha=0のピクセルのRGBを強制的に0(黒)にして圧縮率を高める"""
        mask = img_np[:, :, 3] == 0
        img_np[mask, 0:3] = 0
        return img_np

    def _quadtree_chunk(self, data_mv: memoryview, w: int, h: int, x: int, y: int, cw: int, ch: int, min_size: int = 32) -> list[tuple[int, int, int, bytes]]:
        """
        QuadTree分割: 領域が単色なら巨大なまま返し、複雑なら4分割する。
        戻り値: list of (x, y, rows, chunk_data)
        """
        chunk_data = bytearray(cw * ch * 4)
        row_bytes = w * 4
        offset = 0
        for cy in range(ch):
            start = (y + cy) * row_bytes + x * 4
            chunk_data[offset:offset+cw*4] = data_mv[start:start+cw*4]
            offset += cw * 4
            
        is_solid = (chunk_data == chunk_data[:4] * (len(chunk_data) // 4))
        
        # 単色、または最小サイズに達していればこれ以上分割しない
        if is_solid or (cw <= min_size and ch <= min_size):
            return [(x, y, ch, bytes(chunk_data))]
            
        # 複雑なので4分割
        hw, hh = cw // 2, ch // 2
        chunks = []
        chunks.extend(self._quadtree_chunk(data_mv, w, h, x, y, hw, hh, min_size))
        chunks.extend(self._quadtree_chunk(data_mv, w, h, x + hw, y, hw, hh, min_size))
        chunks.extend(self._quadtree_chunk(data_mv, w, h, x, y + hh, hw, hh, min_size))
        chunks.extend(self._quadtree_chunk(data_mv, w, h, x + hw, y + hh, hw, hh, min_size))
        return chunks

    def _compress_chunk_apple_format(self, chunk_data: bytes, width: int, height: int) -> bytes:
        """
        Appleの dmp2 フォーマットに従ってチャンクをシリアライズする。
        """
        if lzfse is None:
            # フォールバック (非圧縮 v1_raw 相当)
            # 実際には dmp2mini モジュール等を使うが、プロトタイプとしてRawを返す
            return b"dmp2" + struct.pack("<4BHHHH", 4, 1, 10, 4, width, height, 1, 4) + chunk_data[:4] + struct.pack("<I", len(chunk_data)) + chunk_data
            
        # 1. 完全単色判定 (RLE / Apple v3_mini_color)
        if chunk_data == chunk_data[:4] * (len(chunk_data) // 4):
            # 単色はインデックスなしの特殊形式で極小化できる
            indices = b"\x00" * (width * height)
            stream = lzfse.compress(indices)
            return (b"dmp2" + bytes((4, 1, 10, 4)) + struct.pack("<HHHH", width, height, 1, 4)
                    + chunk_data[:4] + struct.pack("<I", len(stream)) + stream)
        
        # 2. LZFSE 圧縮
        comp = lzfse.compress(chunk_data)
        
        # 3. 圧縮負け判定 (フォールバック)
        if len(comp) >= len(chunk_data):
            # LZFSEでサイズが膨らむなら非圧縮 Raw ストリームとして保存
            # Appleのフォーマットでは、非圧縮ストリームも 'bvxn' マジックのLZFSEコンテナで包む必要がある
            from actool_linux.stable.lzfse_compat import _UNCOMPRESSED_MAGIC, _END_OF_STREAM_MAGIC
            raw_stream = _UNCOMPRESSED_MAGIC + struct.pack("<2I", len(chunk_data), len(chunk_data)) + chunk_data + _END_OF_STREAM_MAGIC
            return b"dmp2" + struct.pack("<4BHHHH", 4, 1, 10, 4, width, height, 1, 4) + b"\x00\x00\x00\x00" + struct.pack("<I", len(raw_stream)) + raw_stream
            
        # 成功したLZFSEストリーム
        return b"dmp2" + struct.pack("<4BHHHH", 4, 1, 10, 4, width, height, 1, 4) + b"\x00\x00\x00\x00" + struct.pack("<I", len(comp)) + comp

    def encode(self, data: bytes, w: int, h: int) -> bytes:
        """
        画像をチャンクに分割し、KCBC (Apple Chunked Bitmap) フォーマットのバイナリを生成する。
        """
        img_np = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4)).copy()
        
        if self.clean_alpha:
            img_np = self._clean_dirty_transparency(img_np)
            
        # Appleの標準仕様では、CBCKは縦の帯状（例: w x 64）のチャンクが期待されることがあるが、
        # ここでは我々の最強最適化である QuadTree チャンクを生成する。
        mv = memoryview(img_np.tobytes())
        
        # チャンクの取得
        raw_chunks = self._quadtree_chunk(mv, w, h, 0, 0, w, h, min_size=32)
        
        # バイナリの構築
        encoded_chunks = []
        for x, y, rows, c_data in raw_chunks:
            # AppleのKCBCチャンク構造: KCBC + x, y, rows, payload_size + payload
            dmp2_payload = self._compress_chunk_apple_format(c_data, w, rows)
            # KCBC Header (Magic + x, y, rows, size)
            # ※ Apple純正は x=0, y=0, rows=N が多いが、フォーマットはXY座標をサポートしている
            blob = struct.pack("<4I", 1, 4, len(dmp2_payload), 0) + dmp2_payload
            encoded_chunks.append(b"KCBC" + struct.pack("<4I", x, y, rows, len(blob)) + blob)
            
        # 全チャンクを MLEC (Multi-Level Encoding Container) で包む
        mode_field = 3 # CBCK Mode
        payload = b"MLEC" + struct.pack("<3I", mode_field, 11, len(encoded_chunks)) + b"".join(encoded_chunks)
        
        return payload

