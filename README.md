# Agent Art Signature Prototype

An interactive design panel for developing a deterministic, text-seeded Bézier signature prototype.

The panel converts an X handle and a `gr0k_raw` seed into a reproducible curve using SHA-256-labeled random values, character geometry, serial digit pulses, and selectable SVG path construction.

## Prototype design panel

This page is a design panel for developing the Signature prototype. Every button, toggle, and slider selects a fixed value or a PRNG range for the final algorithm.

The single canvas previews one handle and one `gr0k_raw` seed at a time. Independent gr0k shift controls adjust rotation, handle length, character Y, gap spacing, serial Y, serial width, and serial pulse height while preserving the underlying canonical identity. The final generative process remains one X handle plus one gr0k seed as input and one deterministic SVG/PNG artwork as output.

## Files

- `index.html` — standalone browser panel
- `src/text-seeded-bezier-line.html` — editable visualization source
- `algorithm/signature_algorithm_v1.py` — frozen Signature algorithm `1.0.0`
- `algorithm/signature_algorithm_v1.json` — frozen settings and output rules
- `algorithm/SHA256SUMS` — release-file verification hashes

## Use

Open `index.html` in a browser. Adjust the selected parameters, change the gr0k seed, switch through preset handles, and copy the current SVG.

The signature always originates in a fixed 420 × 420 canonical design space, while the default output is 1080 × 1080. The panel’s output-size fields may request any positive square or rectangular canvas. Square outputs retain the canonical `viewBox` and change only the SVG dimensions. Non-square outputs uniformly scale and center the unchanged canonical curve on a background that fills the requested canvas, so no geometry is stretched or regenerated. The displayed handle remains centered at 95% of the requested output height.

The frozen Python generator accepts the same dimensions:

```sh
python3 algorithm/signature_algorithm_v1.py inshell_art --gr0k-raw 22 --width 1200 --height 800 --output signature.svg
```

The canonical design space is 420 × 420 units. The default SVG output is 1080 × 1080 pixels and may be rendered to a PNG of the same requested output size.

## Reusing the curve system for longer text

The Signature entry point remains strictly limited to an X handle of 1–15 characters. For a separate text-to-curve application, `reusable_text_curve_layout(character_count)` defines the required expansion policy. Above 15 characters, the reference segment width stays at `300 / 14` canonical units. The total curve span and canonical canvas width grow with the number of segments instead of compressing additional anchors into the Signature’s original 300-unit curve span.
