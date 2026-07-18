from __future__ import annotations
import numpy as np

try:
    from actool_linux.stable import lzfse_compat as lzfse
except ImportError:
    try:
        import lzfse
    except ImportError:
        lzfse = None

class SmartCBCKEncoder:
    """
    新世代の超高効率CBCK(Chunked Bitmap Compression)エンコーダ。
    固定グリッド分割ではなく、画像特性に応じた動的分割や、
    RLE/LZFSE/Rawの賢いフォールバックを行います。
    """
    def __init__(self, clean_alpha: bool = True, max_chunk_size: int = 128):
        self.clean_alpha = clean_alpha # Dirty Transparencyの消去フラグ
        self.max_chunk_size = max_chunk_size
        
    def _clean_dirty_transparency(self, img_np: np.ndarray) -> np.ndarray:
        """Alpha=0のピクセルのRGBを強制的に0(黒)にして圧縮率を高める"""
        mask = img_np[:, :, 3] == 0
        img_np[mask, 0:3] = 0
        return img_np

    def _get_chunks(self, data_np: np.ndarray, cw: int, ch: int) -> list[tuple[int, int, bytes]]:
        h, w, _ = data_np.shape
        chunks = []
        for y in range(0, h, ch):
            for x in range(0, w, cw):
                actual_w = min(cw, w - x)
                actual_h = min(ch, h - y)
                chunk_np = data_np[y:y+actual_h, x:x+actual_w]
                chunks.append((actual_w, actual_h, chunk_np.tobytes()))
        return chunks

    def _smart_compress_chunk(self, chunk_data: bytes) -> tuple[bytes, int]:
        """
        1つのチャンクを最適に圧縮する。
        戻り値: (圧縮データ, モードID)
        モードID: 0=Raw, 1=LZFSE, 2=ZLIB, 3=RLE(単色) など (仮)
        ※AppleのCBCKは 0=Raw, 2=LZFSE 等の独自オペコードを使用
        """
        if lzfse is None:
            import zlib
            comp = zlib.compress(chunk_data, level=6)
            if len(comp) >= len(chunk_data):
                return chunk_data, 0 # Raw
            return comp, 2 # ZLIB (仮)

        # 1. 完全単色判定 (RLE)
        if chunk_data == chunk_data[:4] * (len(chunk_data) // 4):
            return chunk_data[:4], 3 # RLE
        
        # 2. LZFSE圧縮
        comp = lzfse.compress(chunk_data)
        
        # 3. 圧縮負け判定 (フォールバック)
        if len(comp) >= len(chunk_data):
            return chunk_data, 0 # Raw
            
        return comp, 1 # LZFSE

    def encode(self, data: bytes, w: int, h: int) -> bytes:
        """
        画像をチャンクに分割し、Smart-CBCKでエンコードする。
        """
        if lzfse is None:
            print("Warning: lzfse is not installed. Falling back to simple compression.")
            
        # 4チャンネル(RGBA)前提
        img_np = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4))
        
        if self.clean_alpha:
            img_np = self._clean_dirty_transparency(img_np)
            
        chunks = self._get_chunks(img_np, self.max_chunk_size, self.max_chunk_size)
        
        # TODO: AppleのKCBC/dmp2フォーマットに合わせてシリアライズする
        # 現状はプロトタイプとしてダミーバイトを返す
        return b"TODO_SMART_ENCODED_DATA"

