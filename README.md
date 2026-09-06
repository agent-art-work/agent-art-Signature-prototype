# Agent Art Signature Prototype

An interactive design panel for developing a deterministic, text-seeded Bézier signature prototype.

The panel converts an X handle and a `gr0k_raw` seed into a reproducible curve using SHA-256-labeled random values, character geometry, serial digit pulses, and selectable SVG path construction.

## Prototype design panel

This page is a design panel for developing the Signature prototype. Every button, toggle, and slider selects a fixed value or a PRNG range for the final algorithm.

The single canvas previews one handle and one `gr0k_raw` seed at a time. Independent gr0k shift controls adjust rotation, handle length, character Y, gap spacing, serial Y, serial width, and serial pulse height while preserving the underlying canonical identity. The final generative process remains one X handle plus one gr0k seed as input and one deterministic SVG/PNG artwork as output.

## Files

- `index.html` — standalone browser panel
- `src/text-seeded-bezier-line.html` — editable visualization source

## Use

Open `index.html` in a browser. Adjust the selected parameters, change the gr0k seed, switch through preset handles, and copy the current SVG.

The canonical artwork canvas and final PNG target are both 420 × 420 pixels.
