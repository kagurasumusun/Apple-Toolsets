with open("wiki/Home.md", "r") as f:
    content = f.read()

content = content.replace("`5_research_reports/` ディレクトリには、Apple純正ツールとの比較マトリクス（数百のJSON）や、CBCKの限界閾値などの生データが保存されています。", "[📊 Research Data Index](5_research_reports/INDEX.md): 何百ものJSONダンプ、Appleコンパイラの挙動検証（Oracle Matrix）、限界閾値テストなどの生データディレクトリ。")

with open("wiki/Home.md", "w") as f:
    f.write(content)
