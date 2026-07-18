# Module: `dmp2mini`\n\n## Overview\ndmp2 "mini" grammars observed in Apple-produced cars (small deepmap comp).

Apple switches dmp2 payload grammar by payload size for near-uniform
sources. All rules below were extracted purely from observable artefacts
(Apple actool outputs; probe suites hp9/hp10 + probe5/probe6 corpus). No
Apple code was consulted.

Observed grammar families (all sharing the dmp2 (v,1,10,bpp) w,h header):

* v1 "raw": ``dmp2 01 01 0a bpp, w, h, pixels`` — no length field, pixels
  begin at offset 12 and run to the end of the frame.
* v3-mini (1-swatch color): ``e4 BGRA ff 38 04 <run tokens> e3 GRA ff 06
  00*7`` where the run tokens cover the byte count 4*px: first token value
  = bytes-33 (cap 255), each continuation = remaining-16 (cap 255).
  Probed range: 9..128 px (36..512 raw bytes). Frame body length L ==
  len(stream incl. the 06 + 7 trailing zeros).
* v3-mini (GA): ``98 02 g a <run tokens> e1 a 06 00*7``; tokens cover the
  byte count 2*px: first = bytes-25 (cap 255), continuations = rem-16
  (cap 255). Verified up to 3200 bytes (40x40). Mode (MLEC) stays 2 for
  opaque, 0 for translucent (gt_ oracles).
* v4-mini (1-swatch palette variant of the v4 grammar): same frame header
  as v4 palette (count=1, bpp=4, one swatch) but the LZFSE stream is
  replaced by ``68 01 00 <run tokens> <end> 06 00*7`` with PIXEL-based
  tokens: first token covers value+27 pixels for even totals, value+26
  for odd totals (probed: u16 256px -> f0 e5, c039 17x15 255px -> f0 e5),
  continuations cover value+16 (value cap 255), and a trailing remainder
  of 3..15 pixels on odd totals is emitted as a bare short token ``fX``
  covering X+2 (probed: u17 17x17 289px -> ``f0 ff f6``). End marker:
  npix even -> ``e2 00 00`` (6 sizes probed), npix % 4 == 3 -> ``e1 00``
  (probed: 255px), npix % 4 == 1 -> ``e3 00 00 00`` (probed: 289px); the
  mod-4 correlation is a two-point fit, extrapolation beyond the probed
  odd sizes 255/289 is inferred. Probed total range: 144..2304 px uniform
  color (u12..u48 oracles; 4096px u64 moves to the v4 LZFSE form). A
  remainder of 2 after the greedy split (or rem==1) cannot use the bare
  form (``f0``/``f1`` are ambiguous); we rebalance the previous long token
  instead — no Apple oracle for that split, stream stays decodable
  (documented inference).

Multi-swatch mini opcodes (e7/e8 intros, 38/28/f1/f2/f3 pattern tokens)
exist for small 2-3-swatch sources (chk04 oracle, k_/t_ probes) but their
token grammar is not fully decoded -> documented gap; we keep emitting the
(accepted) v4-LZFSE form there.

Boundary table (probed endpoints; conservative activation ranges):
  color v1-raw: px <= 8            (8 px v1, 9 px v3-mini)
  color v3-mini: 36B <= B <= 512B  (9..128 px)
  color v4-mini: px >= 144         (144..2304 px probed; 4096 px -> LZFSE)
  GA v1-raw: B <= 8                (4 px), GA v3-mini probed 32B..3200B
  Larger sources fall back to the LZFSE frames (v2/v3/v4) — Apple too.

Emitted substitutes for ranges not yet probed remain the LZFSE frames,
which assetutil/CoreUI accept everywhere (parity gap = payload bytes only).\n\n## Public Functions\n### `v1_raw()`\n\n### `v3_mini_color()`\n``bgra`` is the single premultiplied pixel (4 bytes).\n\n### `v3_mini_ga()`\n``ga`` is the single premultiplied pixel (gray, alpha).\n\n### `v4_mini()`\n1-swatch variant of the v4 palette grammar with mini-RLE stream.

Odd pixel counts use a first-token bias of 26 (probed c039/u17), a
bare short token for remainders 3..15, and the ``npix % 4`` end marker
table (_V4_END); see the module docstring for probe evidence.\n\n### `decode_mini()`\nDecode the 1-swatch mini frames above. Returns premultiplied pixels
(BGRA or GA) or None for anything outside the understood forms.\n\n