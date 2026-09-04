# Agent Art Signature Prototype

An interactive design panel for developing a deterministic, text-seeded Bézier signature prototype.

The panel converts an X handle into a reproducible curve using SHA-256-labeled random values, character geometry, serial digit pulses, and selectable SVG path construction.

## Prototype design panel

This page is a design panel for developing the Signature prototype. Every button, toggle, and slider selects a fixed value or a PRNG range for the final algorithm.

The four canvases and loaded X handles are preview and comparison tools only. They make it easier to observe how the selected settings behave across different inputs. The final generative process remains one X handle as input and one deterministic SVG/PNG artwork as output.

## Files

- `index.html` — standalone browser panel
- `src/text-seeded-bezier-line.html` — editable visualization source

## Use

Open `index.html` in a browser. Adjust the selected parameters, inspect four examples in the 2×2 canvas grid, switch through the preset handles, and copy the SVG for canvas 01.

The canonical artwork canvas and final PNG target are both 420 × 420 pixels.
