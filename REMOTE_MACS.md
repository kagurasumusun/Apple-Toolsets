# Remote Macs (session record)

This file records the current known Upterm sessions and the local helper/key paths used in this workspace.
It stores **connection metadata only**, not private key contents.

## Local key / helper paths

- private key path: `/home/user/.ssh/upterm_test_ed25519`
- current-host helper: `/home/user/cg_upterm.py`
- legacy-host helper: `/home/user/cg_upterm_legacy.py`

## Current validation host

- session: `xGBjvOFB6rf9fCdPeiIx`
- ssh target: `xGBjvOFB6rf9fCdPeiIx@uptermd.upterm.dev`
- repo path: `/Users/runner/work/mac/mac`
- observed OS: macOS `26.4`
- observed default Xcode: `26.5 (17F42)`

Direct command form:

```bash
ssh -i /home/user/.ssh/upterm_test_ed25519 \
  -o IdentitiesOnly=yes -tt \
  xGBjvOFB6rf9fCdPeiIx@uptermd.upterm.dev
```

## Legacy reference host

- session: `ZKPsRZJmMFe9fux0eiMB`
- ssh target: `ZKPsRZJmMFe9fux0eiMB@uptermd.upterm.dev`
- repo path: `/Users/runner/work/mac/mac`
- observed OS: macOS `14.8.7`
- observed installed Xcodes: `15.0`–`15.4`, `16.1`–`16.2`

Direct command form:

```bash
ssh -i /home/user/.ssh/upterm_test_ed25519 \
  -o IdentitiesOnly=yes -tt \
  ZKPsRZJmMFe9fux0eiMB@uptermd.upterm.dev
```

## Notes

- Upterm sessions are temporary and may expire; update this file when new sessions are issued.
- Do not commit private key material itself.
- The authoritative continuation record remains:
  - `CONTINUATION_MEMO_2026-07-13.md`
  - `HANDOFF.md`
  - `SESSION_HANDOFF_COMPLETE.md`
  - `PROJECT_STATE.json`
