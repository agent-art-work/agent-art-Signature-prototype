# Agent Art Signature Prototype

Signature v2.0.0 is a deterministic X-handle + MBTI generative-art system. It converts one X handle and one of the 16 MBTI types into a reproducible SVG signature curve.

## Signature v2.0.0 design panel

The browser page is the prototype design panel for Signature v2.0.0. Its controls expose the fixed values and deterministic PRNG ranges frozen in the renderer. The canvas previews one preset X handle and one selected MBTI type, and it can also show all 16 MBTI results for the current handle.

MBTI controls four independent parts of the result:

- E / I — light or dark field polarity
- S / N — handle length, rotation, neighbor smoothing, handle balance, and digit pulse handles
- T / F — sampled linear `L` outline or cubic Bézier `C` outline
- J / P — ordered or randomized X rhythm and the point-Y distribution

The SHA-256-labeled PRNG remains scoped by semantic parameter labels and X-handle content. MBTI selects the frozen ranges and rendering rules; it is not added to the hash payload.

## Files

- `index.html` — standalone Signature v2.0.0 browser panel
- `src/signatures-mbti-panel.html` — editable Signature v2.0.0 panel source
- `algorithm/signature_renderer_v2.0.0.py` — frozen Signature v2.0.0 Python renderer
- `algorithm/signature_renderer_v2.0.0.json` — frozen v2.0.0 settings, inputs, and MBTI mapping
- `algorithm/signature_algorithm_v1.py` and `.json` — preserved Signature v1.0.0 renderer and settings
- `algorithm/SHA256SUMS` — release-file verification hashes

## Generate a Signature v2.0.0 SVG

The handle must contain 1–15 ASCII letters, digits, or underscores and must not include `@`. The MBTI type must match `^[EI][SN][TF][JP]$`.

```sh
python3 algorithm/signature_renderer_v2.0.0.py inshell_art --mbti INFP --output signature.svg
```

The default output is 1080 × 1080. A rectangular output can be requested without stretching or regenerating the canonical geometry:

```sh
python3 algorithm/signature_renderer_v2.0.0.py inshell_art --mbti ENTJ --width 1200 --height 800 --output signature.svg
```

## Output sizing

Every signature is constructed in a 420 × 420 canonical design space. Square outputs retain the canonical `viewBox` and change the SVG dimensions. Non-square outputs uniformly scale and center the unchanged canonical curve on a background that fills the requested canvas. The displayed handle remains centered at 95% of the requested output height.

## Version verification

Release hashes in `algorithm/SHA256SUMS` verify the frozen Python renderer, JSON settings, panel source, and deployed standalone panel. Git tag `v2.0.0` identifies this release; tag `v1.0.0` preserves the previous gr0k-based algorithm.
