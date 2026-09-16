# Agent Art Signature Prototype

Signature v2.0.1 is a deterministic X-handle + MBTI generative-art system. It converts one X handle and one of the 16 MBTI types into a reproducible SVG signature curve.

## Signature v2.0.1 design panel

The browser page is the prototype design panel for Signature v2.0.1. Its controls expose the fixed values and deterministic PRNG ranges frozen in the renderer. The canvas previews one preset X handle and one selected MBTI type, and it can also show all 16 MBTI results for the current handle.

MBTI controls four independent parts of the result:

- E / I — light or dark field polarity
- S / N — handle length, rotation, neighbor smoothing, handle balance, and digit pulse handles
- T / F — sampled linear `L` outline or cubic Bézier `C` outline
- J / P — ordered or randomized X rhythm and the point-Y distribution

The SHA-256-labeled PRNG remains scoped by semantic parameter labels and X-handle content. MBTI selects the frozen ranges and rendering rules; it is not added to the hash payload.

## Files

- `index.html` — standalone Signature v2.0.1 browser panel
- `src/signatures-mbti-panel.html` — editable Signature v2.0.1 panel source
- `algorithm/signature_renderer_v2.0.1.py` — frozen Signature v2.0.1 Python renderer
- `algorithm/signature_renderer_v2.0.1.json` — frozen v2.0.1 settings, inputs, MBTI mapping, and external long-text layout policy
- `algorithm/signature_renderer_v2.0.0.py` and `.json` — preserved Signature v2.0.0 renderer and settings
- `algorithm/signature_algorithm_v1.py` and `.json` — preserved Signature v1.0.0 renderer and settings
- `algorithm/SHA256SUMS` — release-file verification hashes

## Generate a Signature v2.0.1 SVG

The handle must contain 1–15 ASCII letters, digits, or underscores and must not include `@`. The MBTI type must match `^[EI][SN][TF][JP]$`.

```sh
python3 algorithm/signature_renderer_v2.0.1.py inshell_art --mbti INFP --output signature.svg
```

The default output is 1080 × 1080. A rectangular output can be requested without stretching or regenerating the canonical geometry:

```sh
python3 algorithm/signature_renderer_v2.0.1.py inshell_art --mbti ENTJ --width 1200 --height 800 --output signature.svg
```

## Output sizing

Every signature is constructed in a 420 × 420 canonical design space. Square outputs retain the canonical `viewBox` and change the SVG dimensions. Non-square outputs uniformly scale and center the unchanged canonical curve on a background that fills the requested canvas. The displayed handle remains centered at 95% of the requested output height.

## Reusing the curve system for text longer than 15 characters

The official Signature input remains an X handle of 1–15 characters. The panel and Python Signature entry points reject longer input rather than compressing it into the 300-unit curve span.

If another application reuses the curve system for non-X-handle text longer than 15 characters, it must preserve the reference segment width and expand the horizontal design space:

```text
reference segment width = 300 / (15 - 1) = 21.428571428571427
extended curve span = reference segment width × (character count - 1)
extended canonical width = extended curve span + 120
canonical height = 420
```

The height, handle geometry, stroke widths, and other vertical proportions remain canonical. Only the curve span and canvas width grow, with the original 60-unit margin retained on each side. For a proportional default output, keep the output height at 1080 and calculate `output width = round(1080 × extended canonical width / 420)`.

The Python function `reusable_text_curve_layout(character_count)` and the panel API function `reusableTextCurveLayout(characterCount)` return this layout policy. They do not change the official Signature input contract or silently render long text through the fixed-width Signature entry point.

## Version verification

Release hashes in `algorithm/SHA256SUMS` verify the frozen Python renderers, JSON settings, current panel source, and deployed standalone panel. Git tag `v2.0.1` identifies this patch; tags `v2.0.0` and `v1.0.0` preserve the earlier releases.
