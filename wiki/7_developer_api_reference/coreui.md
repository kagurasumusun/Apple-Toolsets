# Module: `coreui`\n\n## Overview\nCoreUI dialect profiles and version-dependent constants.

Every CoreUI-version-sensitive value the writer emits is centralized here so
tracking a future CoreUI/Xcode release means editing one table, not hunting
through the writers. All values derive from observable Apple output bytes
(CAR files and assetutil dumps produced by Xcode 16.4 / 26.5 oracles on
independently created input catalogs). No Apple code or binaries are copied.

Profile history observed so far:

===================  =====================  ============  ================
oracle               CARHEADER              program tag   trailing u32x4
===================  =====================  ============  ================
Xcode 16.4 (macOS15) ``918, 17, 0, n``       ``918.5``     ``0, 5, 1, 1``
Xcode 26.5 macosx    ``975, 17, 0, n``       ``975 [LAR]`` ``0, 2, 1, 1``
Xcode 26.5 ios/tvos  ``975, 17, 0, n``       ``975``       ``0, 2, 1, 2``
===================  =====================  ============  ================

Apple also stamps a provenance comment ``Xcode 26.5 (17F42) via
AssetCatalogAgent-AssetRuntime`` (macosx) resp. ``...SimulatorAgent``
(ios/tvos). This implementation writes its own provenance string instead;
the profile only records the *observed* agent token because the last header
word correlates with it (1 = AssetRuntime, 2 = Simulator agent).\n\n## Classes\n### `CoreUIProfile`\nOne observed CoreUI output dialect.\n\n**Methods:**\n- `program_string()`\n- `writer_comment()`\n\n## Public Functions\n### `profile_for_platform()`\nObserved per-platform header dialect for the current CoreUI (975).\n\n### `auto_select_profile()`\nSelect the historical or current CoreUI profile based on deployment target and platform.\n\n### `resolve_profile()`\nNormalize a user-supplied profile choice.

``None`` selects the current dialect for ``platform``; a string looks up
:data:`PROFILES` (aliases allowed); a profile instance passes through.\n\n