# Module: `compiler`\n\n## Classes\n### `CompileOptions`\n\n### `CompileResult`\n**Methods:**\n- `ok()`\n\n## Public Functions\n### `compile_brand_assets()`\nCompile a tvOS .brandassets directory (roles: app icon stacks + shelves).

Observed materialization gate (Xcode 26.x): only when
`--target-device tv` and `--app-icon <brand name>` are both passed does
Apple actool emit a CAR for public .brandassets content.\n\n### `compile_catalogs()`\n\n