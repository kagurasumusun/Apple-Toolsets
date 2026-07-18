# Module: `appicons`\n\n## Overview\nDeterministic compatibility AppIcon sidecar manifests and source ranking.\n\n## Public Functions\n### `app_icon_entry_rank()`\nReturn a deterministic preference rank for one AppIcon Contents.json entry.

``None`` means the slot does not apply to the requested platform at all.
Higher scores are preferred. Platform-tagged marketing slots rank above
plain generic/universal slots so mixed multi-platform icon sets choose the
expected source before falling back to area-based tie-breaking.

Observable Xcode behavior also shows that watch-marketing slots in the
compiler path are accepted syntactically but do not materialize Assets.car
or sidecar output for the tested watchOS cases, so they are treated as
non-applicable here.\n\n### `app_icon_sidecar_specs()`\n\n