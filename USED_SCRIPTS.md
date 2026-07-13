# Scripts used during reverse engineering and validation

All reusable scripts used in the recorded work are included under `tools/`. Session transport helpers that originally lived at `/home/user` are copied under `tools/session_helpers/` so the ZIP is self-contained.

## Apple/Xcode behavior probes

- `tools/actool_contract.py` — captures help/version/no-input/unknown-input behavior across installed Xcodes.
- `tools/diagnostic_probe_matrix.py` — schema-3 malformed catalog and diagnostic ordering oracle; supports `ACTOOL_COMMAND` replay.
- `tools/corrupt_diagnostic_probe.py` — corrupt payload, color, UTI, AppIcon, duplicate-name and dynamic-stderr contracts.
- `tools/option_cross_product.py` — bounded platform/option cross-product across selected Xcode apps; supports local command replay.
- `tools/xcode_version_probe.py` — captures byte-exact version plists from installed Xcodes.
- `tools/xcode_matrix.py` — Xcode × SDK actool build matrix.
- `tools/oracle.py` — general fixture/oracle command recorder.

## Apple consumer validation

- `tools/apple_consumer_matrix.py` — opens generated CARs through SDK-specific Apple readers.
- `tools/compare_assetutil.py` — compares local CAR interpretation with Apple `assetutil` metadata.
- `tools/runtime_consumer_matrix.py` — builds, installs, launches, materializes, screenshots and cleans iOS/tvOS/watchOS/visionOS Simulator consumers.
- `tools/simulator_runtime_matrix.py` — inventories and optionally boots every compatible Simulator runtime.

## Codec and rendition probes

- `tools/deepmap_probe.py` — GA8/deepmap fixtures.
- `tools/deepmap_ga16_probe.py` — 16-bit grayscale-alpha fixtures.
- `tools/deepmap_rgb_probe.py` — RGB/deepmap fixtures.
- `tools/deepmap_rgba_probe.py` — RGBA/premultiplication fixtures.
- `tools/cbck_threshold_probe.py` — image dimensions around inferred CBCK raw-byte/row boundaries across selected Xcodes.
- `tools/palette_probe.py` — generated indexed-PNG compression selection matrix.
- `tools/palette_fixture_scan.py` — scans installed Apple CARs for observable legacy `palette-img` records.

## Private compositor / CoreUI observable probes

- `tools/coreui_capabilities.py` — records hashes and matched capability strings without redistributing Apple binaries.
- `tools/compositor_oracle_probe.py` — controlled tvOS brand/Top-Shelf and visionOS layered oracle attempt.
- `tools/layer_stack_fixture_scan.py` — scans installed CARs for Layer Stack/Icon Layer Stack/Solid Layer Stack records.

## Handoff and integrity

- `tools/verify_handoff.py` — verifies required handoff files and all SHA-256/size entries in `EVIDENCE_MANIFEST.json`.

## Session transport helpers

- `tools/session_helpers/run_upterm_command.py` — safely sends a bounded command to the shared Upterm tmux session without using `exit`/`logout`.
- `tools/session_helpers/run_upterm_interrupt.py` — interrupt helper reserved for a genuinely stuck foreground command.

The session helpers are operational tooling, not part of the installed `actool-linux` package. Always protect the SSH identity first:

```bash
chmod 600 /home/user/.ssh/arena_upterm_ed25519
```

Never embed or package the private SSH key itself.
