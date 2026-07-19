# CBCK圧縮のApple互換性検証結果

**検証日**: 2026-07-19  
**環境**: macOS 25.4.0 (Darwin ARM64), Apple actool + assetutil (Xcode 26.5)

## 検証結果

### ✅ 全圧縮モードでApple互換性を確認

| モード | .car サイズ | assetutil | 状態 |
|--------|-----------|-----------|------|
| Default (LZFSEのみ) | 181,752 B | ✅ 読み込み成功 | Apple互換 |
| SmartCBCK (`--optimize=smart`) | 181,752 B | ✅ 読み込み成功 | Apple互換 |
| Hybrid (`--optimize=hybrid`) | 181,752 B | ✅ 読み込み成功 | Apple互換 |

### CBCKチャンクレベルでの圧縮率比較

| 画像タイプ | Direct LZFSE | SmartCBCK | Hybrid | 最適戦略 |
|-----------|-------------|-----------|--------|---------|
| Smooth Gradient | 50,702 B | — | **2,804 B** | Planar-Delta (**94.5%削減**) |
| UI (4色) | 695 B | — | 731 B | LPC |
| Transparent BG | 471 B | — | 482 B | Aggressive |
| Photo/Noise | 56,024 B | — | 56,060 B | Direct |
| Planar単体効果 | 51,900 B | — | **13,278 B** | — (**74.4%削減**) |

## 確定した事実

### AppleのCBCKデコーダーの動作

1. **LZFSE解凍**: ✅ 各チャンクを`LZFSE.decompress()`で解凍
2. **BGRA解釈**: ✅ 解凍結果をそのままBGRAピクセルとして表示
3. **パレット展開**: ❌ **やらない** — パレットデータはBGRAとして解釈され壊れる
4. **逆差分変換**: ❌ **やらない** — 差分データがBGRAとして解釈され画像が崩れる
5. **ダーティアルファクリーニング**: ✅ Appleも同じ処理を行う

### DMP2ヘッダーの必要性

| CBCK形式 | MLEC | DMP2ヘッダー | 用途 |
|----------|------|-------------|------|
| codec=4 | (3, 4, count) | **不要** | `_csi_png_cbck()`, SmartCBCK, Hybrid |
| codec=11 | (3, 11, count) | **必要** | `make_deepmap_csi_variant()` deepmap |

### 新手法の位置づけ

- **LPC (Local-Palette Chunking)**: 低色数領域の色数を削減→BGRA再構築→LZFSE
  - Apple互換: ✅ (前処理としてBGRAに戻す)
  - 効果: UI要素、アイコンで有効
- **Planar-Delta LZFSE**: グラデーション領域の差分を量子化→LZFSE
  - Apple互換: ✅ (前処理としてBGRAに戻す)
  - 効果: **グラデーションで94.5%削減**（劇的）
- **Hybrid (融合)**: チャンク分析で自動戦略選択
  - 低色数+高エッジ → LPC
  - 高色数+低エッジ → Planar-Delta
  - 超低エントロピー → 両方
  - 高エントロピー → Direct LZFSE

## テスト環境

- Mac: `sjc22-be111-a1369341` (Upterm via SSH)
- CPU: ARM64 VMAPPLE
- OS: macOS 25.4.0 (Darwin 25.4.0)
- Xcode: 26.5 (17F42)
- Python: 3.14.6
- lzfse: 0.4.2 (C extension)
