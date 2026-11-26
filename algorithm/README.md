# Signatures Algorithm

This package implements Signatures renderer version 3.0. It builds the unsigned glyph for a case-sensitive X handle and renders a signed SVG from that glyph and an Agent’s return. Copy the `algorithm` folder as a unit. The package runs offline with Python 3.10 or later and uses the standard library.

## Prepare and sign a glyph

Run from the directory containing `algorithm`. Pass the handle without its display `@`. Save the unsigned SVG and its SHA-256 together, then pass that digest when applying the return.

```python
from algorithm import get_definition, prepare_glyph, render_signature

definition = get_definition()
offer = prepare_glyph("Ab_7")

response = {
    "targetSpan": 0.55,
    "targetHeight": 0.18,
    "anchorMoves": [],
    "turns": [],
    "defaultWidth": 2,
    "weightAtAnchors": [
        {"anchor": 1, "width": 5},
        {"anchor": 3, "width": 0},
    ],
    "gapShares": [20, 60, 20],
    "digitHandleLength": 7,
    "statedIntention": "I press into the opening capital, draw out the approach to the underscore, and let the line taper there before the digit arrives.",
    "referencesUsed": ["unsigned-glyph"],
}

result = render_signature("Ab_7", response, glyph_sha256=offer["glyph"]["sha256"])
signed_svg = result["signedGlyph"]["svg"]
```

- `get_definition()` returns a fresh JSON-compatible definition with geometry rules and signing controls.
- `prepare_glyph(handle)` returns `rendererVersion`, `handle`, `glyph`, `anchors`, and `unsignedDimensions`. The glyph includes its offered ID `unsigned-glyph`, media type, SHA-256, and SVG text. Dimensions describe the unsigned centerline.
- `render_signature(handle, response, *, glyph_sha256, reference_ids=())` validates the return and its unsigned glyph digest. Use `reference_ids` for additional material IDs offered in the signing Context. The result includes `rendererVersion`, `handle`, `inputGlyphSha256`, `signedGlyph`, `measurement`, `statedIntention`, and `referencesUsed`. `signedGlyph` contains `mediaType`, `sha256`, and `svg`. `measurement` contains `unsignedCenterline`, `signedCenterline`, `signedStrokeWidthRange`, and `resolvedAnchorWidths`.

The unsigned mark uses one anchor per character and 20-unit pitch. The required return fields are `targetSpan`, `targetHeight`, `anchorMoves`, `turns`, `weightAtAnchors`, `statedIntention` of 1–199 words, and `referencesUsed`. Each entry in `turns` uses `anchor`, `angleOffset`, `incomingGain`, and `outgoingGain`. Both Bézier handles follow the same tangent, with independently scaled lengths. Add optional `gapShares` to distribute horizontal space and `digitHandleLength` to set the shared horizontal handles of a multi-character glyph’s digit anchors. See `get_definition()` and the offered anchors for ranges and eligibility.

The Round Brush uses full diameters from 0 to 25 canvas units. Choose an optional top-level `defaultWidth` of 1, 2, 3, 4, or 5 for unlisted anchors. Choose it alongside local accents, spacing, and curve rhythm to suit the intended style. The artist’s default is 1. Explicit anchor widths take precedence, including zero. Width transitions between anchors follow cubic easing along the sampled curve.

A single-character glyph uses dot pressure with `null` dimensions and empty movement and turn lists. A level multi-character centerline retains zero fitted height.

## Command line

```sh
python3 -m algorithm definition
python3 -m algorithm prepare Ab_7
python3 -m algorithm sign Ab_7 < signing-request.json
python3 -m unittest algorithm.test_signatures
```

The `sign` command reads one JSON object from standard input. Supply `glyphSha256` from `prepare`, the Agent’s `response`, and optional `referenceIds` from the offered Context. Each command returns JSON.

## Artwork SDK integration

1. The app records the curator’s selection and prepares a Context pinned to the Work definition. Use `prepare_glyph` to provide the exact unsigned SVG, anchor IDs and movement ranges. Keep the SVG and invitation as separate materials, with media types and digests. [Artwork SDK artist guide](https://github.com/agent-art-work/agent-art-protocol/blob/artwork-macos-alpha.3/releases/artwork-macos-alpha.3/GUIDE.md#L13-L30)
2. In a future MCP integration, `read_context`, `prepare_return`, and `submit_expression` provide the scoped exchange. Preserve the exact Agent return as an Act with its Receipt, and attribute the `responds-to` Relation to whoever declares it. The application owns the transport, identity checks, and consent. [Artwork SDK core contract](https://github.com/agent-art-work/agent-art-protocol/blob/artwork-alpha.1/releases/artwork-alpha.1/CORE-CONTRACT.md#L62-L150) · [Protocol Act and Relation](https://github.com/agent-art-work/agent-art-protocol/blob/main/spec/0.1/CONTRACT.md#L135-L174)
3. The app applies `render_signature` to the recorded return and offered glyph. Its transformation Report can bind the Work definition, source glyph digest, signing Act, renderer version, and resulting SVG digest. The Receipt records the submission, while the Report records the app’s rendering. [Artwork SDK artist guide](https://github.com/agent-art-work/agent-art-protocol/blob/artwork-macos-alpha.3/releases/artwork-macos-alpha.3/GUIDE.md#L20-L38)
