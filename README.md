# Agent Art Signature

An interactive, deterministic text-seeded Bézier signature generator.

The panel converts an X handle into a reproducible curve using SHA-256-labeled random values, character geometry, serial digit pulses, and selectable SVG path construction.

## Files

- `index.html` — standalone browser panel
- `src/text-seeded-bezier-line.html` — editable visualization source

## Use

Open `index.html` in a browser. Adjust the selected parameters, inspect four examples in the 2×2 canvas grid, and copy the SVG, Python art specification, or no-code deterministic specification.

The canonical artwork canvas and final PNG target are both 420 × 420 pixels.
