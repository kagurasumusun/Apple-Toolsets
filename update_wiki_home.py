with open("wiki/Home.md", "r") as f:
    content = f.read()

content += """
### 7. Developer API Reference
`actool_linux.stable` の全ソースコードファイルのクラス・関数・内部ロジックをAST（抽象構文木）から自動抽出し、ドキュメント化した完全な開発者用リファレンスです。
- **[💻 Developer API Index](7_developer_api_reference/INDEX.md)**
"""

with open("wiki/Home.md", "w") as f:
    f.write(content)
