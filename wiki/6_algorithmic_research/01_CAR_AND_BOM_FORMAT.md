# 📦 CoreUI CAR File & BOMStore Architecture

この論文は、Appleのクローズドなアセットカタログ形式である `.car` (CoreUI Archive) ファイルの低レイヤ構造と、その基盤となる `BOMStore` (Bill of Materials) 形式の完全な解剖記録である。

## 1. The BOMStore Container (バイナリコンテナ層)
すべての `.car` ファイルは、Mac OS X 時代から続くパッケージ管理フォーマット `BOMStore` の上に構築されている。BOMはディレクトリ構造をツリー（B-Tree）としてバイナリに格納する非常に堅牢なデータ構造を持つ。

### 1.1 Header Structure (ヘッダ構造)
BOMのファイルは必ず `BOMStore` という8バイトのマジックナンバーから始まる。
```c
struct BOMHeader {
    char magic[8];           // "BOMStore"
    uint32_t version;        // 1
    uint32_t num_blocks;     // 総ブロック数
    uint32_t index_offset;   // ブロックインデックステーブルへのポインタ
    uint32_t index_length;   // インデックステーブルのバイトサイズ
    uint32_t vars_offset;    // 変数テーブルへのポインタ
    uint32_t vars_length;    // 変数テーブルのバイトサイズ
} __attribute__((packed));   // 全て Big-Endian
```

### 1.2 Variables and B-Trees (変数と木構造)
BOMは「ブロック」と呼ばれるデータの塊をID (整数) で管理する。ファイル内の意味のあるデータ（CARヘッダやキーフォーマットなど）は、文字列の変数名(`Variables`)として登録され、ブロックIDと紐付けられる。
主要な変数は以下の通り：
*   `CARHEADER`: CARファイルの基本情報（バージョン、対象OS等）
*   `KEYFORMAT`: アセットを検索するための次元（Idiom, Scale, Appearance等）のレイアウト定義
*   `FACETKEYS`: アセットの名前（文字列）と識別子（整数）のマッピング
*   `RENDITIONS`: 実際のアセットデータ（画像、色、データ）が格納されたB-Tree

## 2. Rendition Keys (アセットの検索次元)
`.car` ファイル内では、画像の名前（例: `AppIcon`）で直接検索することはしない。名前は `FACETKEYS` によって内部の整数IDに変換され、さらに「デバイス(Idiom)」「解像度(Scale)」「テーマ(Appearance)」といった最大20個の次元からなる **Rendition Key** に組み立てられる。

```text
Rendition Key (Example for a Dark Mode iPhone 2x Icon):
- Dimension 1 (Element)   : 12 (Icon)
- Dimension 2 (Part)      : 181 (Facet ID for "AppIcon")
- Dimension 3 (Idiom)     : 1 (iPhone)
- Dimension 4 (Scale)     : 2 (2x Resolution)
- Dimension 5 (Appearance): 1 (Dark Mode)
```

この固定長配列（Key）を使って `RENDITIONS` B-Tree を検索し、マッチしたブロックIDからペイロード（`CSI` 構造）を取得する。

## 3. CoreStructuredImage (CSI) Payload
`RENDITIONS` ツリーから得られたデータは、`ISTC` というマジックナンバーから始まる `CoreStructuredImage` (CSI) 構造体である。

*   **Header**: `ISTC` + Width, Height, Format, Version.
*   **TLVs (Tag-Length-Value)**: Appleは拡張性を担保するため、メタデータ（色空間、スライス情報、EXIF、圧縮アルゴリズム情報など）をすべて可変長のTLV形式でブロックの末尾や中間に埋め込んでいる。
*   **Raw Data**: TLVの後に、いよいよ実際のピクセルデータ（PNG, JPEG, HEIF, あるいは Apple独自の CBCK）が格納される。

---
*Documented by Arena Agent based on clean-room reverse engineering.*
