"""Machine-readable implementation and Apple-verification boundary."""
from __future__ import annotations

CAPABILITIES = {
 "container": {"implemented": True, "apple_assetutil": True, "generations": "CoreUI storage 15-17; Xcode 10-era readers through Xcode 26.5 observed"},
 "images": {"implemented": True, "apple_assetutil": True, "appkit": True, "formats": ["PNG/deepmap2","CBCK/LZFSE","JPEG","HEIF","PDF","SVG"]},
 "symbols": {"implemented": True, "apple_assetutil": True, "scope": "part-59 vectors, 9 weights, S/M/L; advanced effects partial"},
 "packed_atlas": {"implemented": True, "apple_assetutil": True, "scope": "INLK links, deterministic single-page shelf packer; Xcode heuristic not byte-identical"},
 "app_icons": {"implemented": True, "apple_assetutil": True, "platforms": ["iOS","iPadOS","tvOS","watchOS","macOS","visionOS"]},
 "layered_icons": {"implemented": True, "apple_assetutil": True, "scope": "layer/depth keys; proprietary compositor metadata partial"},
 "watch_complications": {"implemented": True, "apple_assetutil": True, "scope": "12 family IDs and 5 role IDs in subtype/dimension2 keys"},
 "thinning": {"implemented": True, "apple_assetutil": True, "scope": "writer-side deterministic selector; exact actool device-model policy partial"},
 "simulator_consumers": {"implemented": False, "verified": ["iOS 26.2 CBCK/UIKit"], "remaining": "all installed iOS/tvOS/watchOS/visionOS runtimes"},
 "diagnostics": {"implemented": False, "scope": "common contracts only; full byte-for-byte corpus incomplete"},
 "cbck_threshold_matrix": {"implemented": False, "scope": "codec implemented; all-Xcode adoption thresholds incomplete"},
 "springboard_dock_comparison": {"implemented": False, "scope": "not yet completed across platforms"},
 "legacy_palette_img": {"implemented": False, "scope": "reader/capability evidence; writer fixture-gated"},
}

def capability_report() -> dict[str, object]:
    return {"tool": "actool-linux", "claims": CAPABILITIES,
            "verified_hosts": ["macOS 15.7.7 / Xcode 16.4 / CoreUI 918.5", "macOS 26.4 / Xcode 26.5 / assetutil 974.1"]}
