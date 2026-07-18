# 🏗 Codebase Architecture & Module Relations

このドキュメントは、`Apple-actool-py` の全ソースコード（ファイル）の役割、内部構造、およびモジュール間の依存関係を徹底的に解説したものです。

## 📁 `actool_linux/stable/` (コアコンパイラ層)
Apple純正 `actool` と1バイトの狂いもなく完全互換のCARファイルを生成するための安定版コード群です。

### 1. The Binary Core (バイナリコンテナ層)
すべてのデータは最終的にこの層を通じてシリアライズされます。
*   **`bom.py` / `bomwriter.py`**
    *   AppleのBOM (Bill of Materials) 形式のパーサーおよびライターです。
    *   `bomwriter.py` は、辞書(Variables)やツリー(Blocks)を正しくBOM構造としてメモリ上にストリーム展開し、`.car` ファイルの土台を作ります。
*   **`car.py` / `carwriter.py` / `carinfo.py`**
    *   `car.py`: 読み込み専用のCARラッパー。
    *   `carwriter.py`: **プロジェクトの心臓部**。BOMWriterを呼び出し、画像データを `_build_assets_car_multilevel` などを用いてTLVs（Tag-Length-Value）形式の `CoreThemeDocument` にパッケージングします。
    *   `carinfo.py`: 解析用。CARの中身をJSONライクな辞書にダンプします。
*   **`csi.py`**
    *   `CoreThemeStructuredImage` 形式の解析。画像以外のベクターやデータアセットのヘッダを読み解きます。

### 2. Compression & Image Formats (圧縮と画像データ層)
*   **`lzfse_compat.py` / `lzfse_optimized.py`**
    *   Appleの標準圧縮アルゴリズムLZFSE。`_compat.py` はC拡張がない場合の安全なフォールバックを担い、`_optimized.py` は純Python環境でのゼロコピー圧縮（メモリビュー利用）を提供します。
*   **`cbck.py` / `cbck_complete.py`**
    *   Chunked Bitmap Compression。巨大な画像をブロックに分け、個別にLZFSEやRLEで圧縮する仕組みです。
*   **`dmp2mini.py`**
    *   Deepmap（画像のピクセルバッファ）の小規模なエンコーディング（v1_raw, v3_mini_color等）をシミュレートします。
*   **`paletteimg.py`**
    *   256色以下の画像をインデックスカラー（パレット）化し、ファイルサイズを削減します。

### 3. The Compiler Pipeline (コンパイラ・ビジネスロジック層)
ユーザーからの入力を解釈し、バイナリコアへ渡すまでの司令塔です。
*   **`cli.py` / `__main__.py`**
    *   コマンドライン引数（`--compile`, `--target-device` 等）をパースし、パイプラインを起動します。
*   **`compiler.py`**
    *   メインのコンパイルロジック。`load_catalog` で読み込んだアセットを順に処理し、AppIconのサイドカー生成、LaunchImageのコピー、そして最終的な `Assets.car` の書き出し（`carwriter`への委譲）を行います。
*   **`model.py`**
    *   `Contents.json` を再帰的に読み込み、アセットディレクトリの名前空間（Namespace）を解決してメモリ上のモデル（`Catalog`, `Asset`）に変換します。
*   **`thinning.py`**
    *   `--target-device iphone` などが指定された際、不要なデバイス向け（iPadやMac）の画像を間引き（Thinning）、CARの容量を削減します。

### 4. Advanced Asset Types (特殊アセット層)
*   **`atlas.py` / `atlas_geometry.py`**
    *   多数の小さな画像を1枚の巨大なテクスチャに敷き詰める（パッキング）処理。`atlas_geometry.py` のスカイライン法で座標を決定します。
*   **`appicons.py`**
    *   AppIconのサイズ検証、プラットフォーム（iOS, macOS, watchOS）ごとの必須サイズの判定とランキングを行います。
*   **`imagestack.py` / `solidstack.py` / `texture_gradient_stack.py`**
    *   tvOSやvisionOS向けの「多層レイヤー画像（3Dで傾くアイコン）」やグラデーションマテリアルをエンコードします。
*   **`pdfcar.py`**
    *   PDF形式のベクター画像から、1x, 2x, 3x のフォールバックPNGを生成してパッキングします。

---

## 🚀 `actool_linux/nextgen/` (次世代コンパイラ層)
Stable版のロジックを継承しつつ、独自の超最適化アルゴリズムをフックするためのディレクトリです。
*   **`smart_cbck.py`**: Dirty Transparency（透明ピクセルの見えないゴミ）の削除や、QuadTree分割によるハイブリッド圧縮を司ります。
*   **`astc_optimizer.py`**: 画像をGPUネイティブなASTC形式に変換し、VRAM消費を1/4にするモジュールのスタブです。

## 🧠 `actool_linux/research/` (研究・AI開発層)
Appleの仕様の限界を突破するための実験コード群です。
*   **`ai_quantizer.py`**: K-Meansを用いて、人間の目には劣化が分からないレベルで画像を強制的に16/256色に減色し、後段の圧縮効率を爆発させます。
*   **`semantic_fusion.py`**: 画像のエッジ密度を分析し、「文字部分は劣化なしLZFSE」「背景はASTC」というように、1つのファイルに複数のフォーマットを継ぎ接ぎ（Fusion）する究極のハイブリッドエンジンです。
