with open("wiki/Home.md", "r") as f:
    content = f.read()

content = content.replace("### 5. Algorithmic Research & Whitepapers (NEW!)", "### 5. Algorithmic Research & Whitepapers (NEW!)\\n- **[📄 05: Facet Hash16 Anatomy & The 100% Accuracy Lookup Table](6_algorithmic_research/05_FACET_HASH16_ANATOMY.md)**: Appleの非公開16ビットハッシュアルゴリズムの解明と、ルックアップテーブルを用いた100%完全一致の仕組み。")

with open("wiki/Home.md", "w") as f:
    f.write(content)
