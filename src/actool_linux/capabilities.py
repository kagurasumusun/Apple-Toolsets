"""Machine-readable implementation and Apple-verification boundary."""
from __future__ import annotations

CAPABILITIES = {
 "container": {"implemented": True, "apple_assetutil": True, "generations": "CoreUI storage 15-17; Xcode 10-era readers through Xcode 26.5 observed"},
 "images": {"implemented": True, "apple_assetutil": True, "appkit": True, "formats": ["PNG/deepmap2","CBCK/LZFSE","JPEG","HEIF","PDF","SVG"]},
 "symbols": {"implemented": True, "apple_assetutil": True, "scope": "part-59 vectors, 9 weights, S/M/L; advanced effects partial"},
 "packed_atlas": {"implemented": True, "apple_assetutil": True, "scope": "INLK links and deterministic bounded multi-page shelf packer Apple-accepted; exact Xcode split/order heuristic not byte-identical"},
 "app_icons": {"implemented": True, "apple_assetutil": True, "platforms": ["iOS","iPadOS","tvOS","watchOS","macOS","visionOS"]},
 "layered_icons": {"implemented": True, "apple_assetutil": True, "scope": "layer/depth keys; proprietary compositor metadata partial"},
 "watch_complications": {"implemented": True, "apple_assetutil": True, "scope": "12 family IDs and 5 role IDs in subtype/dimension2 keys"},
 "thinning": {"implemented": True, "apple_assetutil": True, "scope": "writer-side deterministic selector; exact actool device-model policy partial"},
 "simulator_consumers": {"implemented": True, "verified": ["all 12 installed iOS/tvOS/watchOS/visionOS 26.2/26.4/26.5 runtimes: build, install, launch, materialization, screenshot"], "remaining": "Home/SpringBoard compositor comparison is separate"},
 "diagnostics": {"implemented": False, "scope": "22 focused Xcode 26.5 byte-identical contracts; schema-3 is 18/18; full corpus incomplete"},
 "cbck_threshold_matrix": {"implemented": True, "scope": "Xcode 26.5 iPhoneOS ordinary-image boundary probe 9/9 deepmap2; all-Xcode role-specific matrix incomplete"},
 "springboard_dock_comparison": {"implemented": False, "scope": "not yet completed across platforms"},
 "legacy_palette_img": {"implemented": False, "scope": "reader/capability evidence; writer fixture-gated"},
}

def capability_report() -> dict[str, object]:
    return {"tool": "actool-linux", "claims": CAPABILITIES,
            "verified_hosts": ["macOS 15.7.7 / Xcode 16.4 / CoreUI 918.5", "macOS 26.4 / Xcode 26.5 / assetutil 974.1"]}
