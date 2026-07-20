# ibtool-research

Apple 純正 `ibtool` (Xcode 26.5) の動作研究ノートと出力サンプル集です。

`pyibtool` (pure Python による ibtool 互換実装) の開発のために、

- Apple `ibtool` の man ページ全項目
- 各種 xib → nib compile の出力
- dump 系 (`--all`, `--classes`, `--objects`, `--hierarchy`, ...) の出力
- xliff / strings 等のローカライズ出力
- `--help` / `--version` 等のメタ出力
- Apple nib / storyboardc の構造解析結果

を体系的に収集しました。

## ファイル

- `ibtool_version.txt` - Apple ibtool のバージョン情報
- `man_ibtool.txt` - man ページ全項目
- `otool.txt` - otool との比較
- `summary_results.txt` - 結果サマリ
- `x01_xib_head_ivc.txt` 〜 - Apple ibtool の各種出力サンプル

## 関連プロジェクト

- [pyibtool](https://github.com/kagurasumusun/Apple-Toolsets/tree/main/ibtool-py) - pure Python による ibtool 互換実装 (Apple-Toolsets monorepo)
