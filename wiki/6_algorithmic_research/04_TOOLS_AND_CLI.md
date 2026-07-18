# 🛠 Tools & CLI Architecture

本プロジェクトは単なるライブラリではなく、Apple純正の `actool` や `assetutil` を完全に置き換えることを目的とした堅牢なコマンドラインインターフェース（CLI）を備えています。

## 1. CLI エントリポイント (`actool_linux.stable.cli`)
ユーザーが `actool-linux` コマンドを実行した際の処理フロー：

1. **引数パース (`argparse`)**:
   * Appleの `actool` は非常にレガシーで特殊な引数（例: `--compile out_dir` のように値を後続させる）を取ります。これをPythonの `argparse` で完全に再現しています。
2. **モデル変換 (`model.py`)**:
   * 入力された `.xcassets` カタログディレクトリを再帰的に走査し、`Contents.json` を解釈してメモリ上の `Catalog` および `Asset` クラスにマッピングします。
3. **コンパイラ起動 (`compiler.py`)**:
   * メモリ上のモデルを元に、画像フォーマット（PNG, HEIF, SVG等）に応じたエンコード処理を並列（または順次）で呼び出します。
4. **Thinning（間引き処理） (`thinning.py`)**:
   * `--target-device` 引数が指定された場合、必要なIdiom（例: `iphone` なら Idiom=1）以外のレンディションを破棄し、最終的なCARファイルの容量を削減します。
5. **バイナリパッキング (`carwriter.py` & `bomwriter.py`)**:
   * 最終的なピクセルデータとメタデータ（TLVs）をBOMStoreのブロックとして書き込みます。

## 2. 解析・調査用スクリプト (`scripts/` フォルダ)
リポジトリの `scripts/` ディレクトリには、本プロジェクトを開発するために用いた多数のリバースエンジニアリングツールが格納されています。

* **`legacy_tools/`**:
  * Appleの出力したCARファイルをバイト単位で比較（Diff）するツールや、BOMツリーの構造をJSONにダンプするツールなど、泥臭い調査に使われたスクリプト群です。
* **`evaluate_car_types.py`**:
  * 現在のコンパイラがどのファイルフォーマット（PDF, SVG, Color等）に対応しているかを出力するツールです。

## 3. 次世代パイプライン (NextGen Pipeline)
開発者向けの拡張として、将来的に `--optimize=godmode` のようなフラグが渡された場合、`compiler.py` 内で処理が分岐し、`actool_linux/nextgen/` 以下のカスタムオプティマイザ（ASTC変換やQuadTree分割）が呼び出されるようにアーキテクチャが分離されています。
