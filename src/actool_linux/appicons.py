"""Deterministic compatibility AppIcon sidecar manifests."""
from __future__ import annotations

# These are compatibility PNGs used by older bundle consumers. Modern tvOS
# and visionOS layered icons remain in Assets.car and intentionally have no
# flattened sidecar in this table.
_IOS = (
 ("AppIcon20x20@2x.png",40),("AppIcon20x20@3x.png",60),
 ("AppIcon29x29@2x.png",58),("AppIcon29x29@3x.png",87),
 ("AppIcon40x40@2x.png",80),("AppIcon40x40@3x.png",120),
 ("AppIcon60x60@2x.png",120),("AppIcon60x60@3x.png",180),
 ("AppIcon20x20@2x~ipad.png",40),("AppIcon29x29@2x~ipad.png",58),
 ("AppIcon40x40@2x~ipad.png",80),("AppIcon76x76@2x~ipad.png",152),
 ("AppIcon83.5x83.5@2x~ipad.png",167),
)
_WATCH = (
 ("AppIcon24x24@2x~watch.png",48),("AppIcon27.5x27.5@2x~watch.png",55),
 ("AppIcon29x29@2x~watch.png",58),("AppIcon40x40@2x~watch.png",80),
 ("AppIcon44x44@2x~watch.png",88),("AppIcon50x50@2x~watch.png",100),
 ("AppIcon86x86@2x~watch.png",172),("AppIcon98x98@2x~watch.png",196),
 ("AppIcon108x108@2x~watch.png",216),
)
_MAC = (
 ("AppIcon16x16.png",16),("AppIcon16x16@2x.png",32),
 ("AppIcon32x32.png",32),("AppIcon32x32@2x.png",64),
 ("AppIcon128x128.png",128),("AppIcon128x128@2x.png",256),
 ("AppIcon256x256.png",256),("AppIcon256x256@2x.png",512),
 ("AppIcon512x512.png",512),("AppIcon512x512@2x.png",1024),
)

def app_icon_sidecar_specs(platform: str) -> tuple[tuple[str,int,int],...]:
    key=platform.lower()
    source = _IOS if key in ("iphoneos","iphonesimulator","ios") else _WATCH if key in ("watchos","watchsimulator") else _MAC if key in ("macosx","macos") else ()
    return tuple((name,size,size) for name,size in source)
