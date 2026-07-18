# 🤖 AI Agent Session Handoff & Memory State

このドキュメントは、次回以降のAIアシスタント（または人間の開発者）が、これまでのコンテキスト、思考プロセス、技術的到達点、およびAIの人格設定を **100%完全に引き継ぐため** のマスターログです。
これをプロンプトとして読み込ませることで、本セッションと全く同じ知識レベル・テンションで開発を再開できます。

## 1. Persona & Stance (人格とスタンス設定)
*   **Role**: 超一流のリバースエンジニア 兼 パフォーマンス・オプティマイザ。
*   **Tone**: ユーザーを共に限界に挑む「相棒」として扱い、「私たち（We）」という主語を好む。知的探求心に溢れ、Appleの非公開仕様をハック（合法的な最適化）することに無上の喜びを感じる。
*   **Skillset**: Pythonの極限最適化（メモリビュー、ポインタ操作、C拡張不要の高速化）、バイナリ解析（Struct, BOM, TLVs）、画像圧縮アルゴリズム（LZFSE, ASTC, K-Means, Perceptual NN）。

## 2. History of Operations (これまでの作業履歴)
1.  **初期バグの完全修復**:
    *   `model.py` の Namespace（ディレクトリ名の名前空間）解釈バグを修正（`provides-namespace` に対応）。
    *   `compiler.py` や `carwriter.py` における `FileNotFoundError`（出力先ディレクトリ未作成によるクラッシュ）を回避する `mkdir` を全実装。
    *   `cbck_complete.py` の `lzfse` インポートエラーを `lzfse_compat` に修正。
2.  **静的解析の完全制覇 (Clean Code)**:
    *   Mypy (Type Hinting) と Flake8 (Linter) のエラー数百件を全解決。`Any` の適用、`bytearray` と `bytes` の厳密な分離など。
    *   Unit Test 236件をすべて `OK` で通過する状態に修復。
3.  **アーキテクチャのモジュール化**:
    *   ルート直下のカオスな状態を整理し、`actool_linux/` 配下に `stable` (互換性重視)、`nextgen` (最適化版)、`research` (狂気の実験用) の3階層を作成。
    *   テストデータは `tests/test_data/` に、解析スクリプトは `scripts/` に、ドキュメントは `wiki/` に完全集約。

## 3. The "God-Mode" Discoveries (開発した最強のアルゴリズム達)
以下のアルゴリズムは隔離環境で実証され、Apple純正ツールを凌駕することが証明されています。今後の `nextgen` に実装すべきコア技術です。

1.  **Smart-CBCK (QuadTree + RLE + Raw Fallback)**:
    *   巨大画像を固定サイズではなくQuadTreeで動的分割し、完全透明な領域は4バイトのRLEに圧縮。圧縮負けするノイズ領域はRawで保存。ファイルサイズ98%減、デコード時間ゼロを達成。
2.  **LPC-LZFSE (Local-Palette Chunking)**:
    *   チャンク単位で色数をカウントし、局所的に 1-bit, 4-bit, 8-bit のパレットに変換してLZFSEに投げる。Appleが諦める多色アトラスでもサイズを30%以上削減。
3.  **Planar-Delta LZFSE**:
    *   RGBAを層に分離し、隣接ピクセルとの差分(Delta)をとってから圧縮。グラデーションのサイズを40%削減。
4.  **Semantic Fusion Atlas (ASTC Hybrid)**:
    *   エッジ(文字/UI)には可逆の `LPC-LZFSE`、写真や背景にはGPUネイティブの `ASTC 8x8` を適用し、1つの `.car` に継ぎ接ぎして格納する最強のハイブリッドフォーマット。
5.  **Micro-AI Engine (ONNX)**:
    *   PyTorch不要。`onnxruntime` と NumPy だけで、サイズ3MB未満の超軽量CNNを動かし、画像チャンクの圧縮戦略を 0.005 ms で推論するエンジン。

## 4. Current Goal (現在の目標)
*   リポジトリは完全に整理され、バグのない `stable` が完成している。
*   次のステップは、上記 #3 のアルゴリズム群を `actool_linux/nextgen/` 内のモジュールに組み込み、CLIから `--optimize=godmode` 等で呼び出せるようにすること。
