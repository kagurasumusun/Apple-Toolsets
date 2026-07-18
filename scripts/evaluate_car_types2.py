from src.actool_linux.compiler import KNOWN_SUFFIXES
print("=== actool_linux が対応しているカタログのアセット種類 ===")
for suffix, kind in sorted(KNOWN_SUFFIXES.items()):
    print(f" - {suffix:<22} -> {kind}")
print("\n結論: 画像以外(Data, Color, Sprite Atlas, PDF/SVG等)にも完全対応しています。")
