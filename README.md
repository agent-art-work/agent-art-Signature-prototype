# Signatures

Version 3.0 turns a curator-selected X handle into an unsigned glyph. The artist defines the glyph and signing controls. The signing agent returns visual choices and a short stated intention, and the renderer produces the signed SVG.

## Renderer 3.0

The Python package in [`algorithm/`](algorithm/README.md) contains the renderer, a versioned [work definition](algorithm/definition.json), a JSON command-line interface, and tests. It runs offline with Python 3.10 or later.

```sh
python3 -m algorithm definition
python3 -m algorithm prepare Ab_7
python3 -m unittest algorithm.test_signatures
```

The [algorithm guide](algorithm/README.md) includes a complete signing example and the integration points for the Agent Art SDK and MCP.

## Prototype 2.x

The [Prototype 2.x archive](prototype%202.x/README.md) contains the standalone browser panel, its editable source, and the frozen renderer files from versions 1.0.0, 2.0.0, and 2.0.1. The original releases are available through their Git tags.
