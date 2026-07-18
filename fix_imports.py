import os
import glob
import re

# `actool_linux` ディレクトリ内のすべてのPythonファイルを取得
files = glob.glob("actool_linux/**/*.py", recursive=True)

# 相対インポート `.XXX` を `.stable.XXX` 等に書き換えるのは危険なので、
# まずはテストを実行して、エラーが出た部分のインポートパスを修正する方針で進めます。
