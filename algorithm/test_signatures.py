"""Contract tests for the standalone Signatures renderer."""

import hashlib
import unittest
from xml.etree import ElementTree

from . import get_definition, prepare_glyph, render_signature


SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"
MIXED_HANDLE = "aA0_9"
# Captured from the Point Version renderer before extracting the standalone API.
MIXED_UNSIGNED_SHA256 = "5276dda8f1f3d298d91728b610428553b5efcbd5e5cd0b84cdb4639f16d4cec5"
MIXED_SIGNED_SHA256 = "dc495834c7f3aaad5588473d852b505321c5cb29e749bdbab3355b7e914b1159"


class SignaturesTest(unittest.TestCase):
    def response(self, **overrides):
        return {
            "targetSpan": 0.62,
            "targetHeight": 0.25,
            "anchorMoves": [],
            "turns": [],
            "weightAtAnchors": [],
            "statedIntention": "I press the first stroke firmly and let it thin toward the zero.",
            "referencesUsed": ["unsigned-glyph"],
            **overrides,
        }

    def test_work_definition(self):
        definition = get_definition()
        self.assertEqual(definition["work"]["definitionVersion"], "3.0")
        self.assertEqual(definition["glyphRules"]["anchorsPerCharacter"], 1)
        self.assertEqual(definition["glyphRules"]["strokeWidth"], 1.5)
        weight = definition["controls"]["weightAtAnchors"]
        self.assertEqual(weight["widthRange"], [0, 25])
        self.assertEqual(weight["defaultWidth"], 1)

    def test_mixed_glyph_preserves_case_and_character_positions(self):
        offer = prepare_glyph(MIXED_HANDLE)
        self.assertEqual(offer, prepare_glyph(MIXED_HANDLE))
        self.assertEqual(offer["handle"], MIXED_HANDLE)
        self.assertTrue(offer["rendererVersion"])
        self.assertEqual([anchor["character"] for anchor in offer["anchors"]], list(MIXED_HANDLE))
        self.assertEqual([anchor["anchor"] for anchor in offer["anchors"]], list(range(1, 6)))
        self.assertEqual([anchor["characterPosition"] for anchor in offer["anchors"]], list(range(1, 6)))
        lower, upper, zero, underscore, nine = offer["anchors"]
        self.assertNotEqual(lower["y"], upper["y"])
        self.assertLess(nine["y"], zero["y"])
        self.assertGreater(underscore["y"], zero["y"])
        self.assertEqual(offer["glyph"]["id"], "unsigned-glyph")
        self.assert_svg(offer["glyph"], MIXED_UNSIGNED_SHA256)

    def test_signing_with_rhythm_turns_and_pressure(self):
        offer = prepare_glyph(MIXED_HANDLE)
        response = self.response(
            anchorMoves=[{"anchor": 2, "dx": 2, "dy": -8}, {"anchor": 4, "dx": -1, "dy": 1}],
            turns=[{"anchor": 2, "angleOffset": -15, "incomingGain": 0.9, "outgoingGain": 1.1}],
            weightAtAnchors=[
                {"anchor": 1, "width": 25}, {"anchor": 2, "width": 2}, {"anchor": 3, "width": 0},
                {"anchor": 4, "width": 2}, {"anchor": 5, "width": 4.5},
            ],
            referencesUsed=["unsigned-glyph", "profile"],
            gapShares=[10, 20, 30, 40],
            digitHandleLength=7,
        )
        result = render_signature(
            MIXED_HANDLE, response, glyph_sha256=offer["glyph"]["sha256"], reference_ids=("profile", "unused"),
        )
        self.assertEqual(result["rendererVersion"], offer["rendererVersion"])
        self.assertEqual(result["handle"], MIXED_HANDLE)
        self.assertEqual(result["inputGlyphSha256"], MIXED_UNSIGNED_SHA256)
        self.assertEqual(result["statedIntention"], response["statedIntention"])
        self.assertEqual(result["referencesUsed"], response["referencesUsed"])
        self.assert_svg(result["signedGlyph"], MIXED_SIGNED_SHA256)
        measurement = result["measurement"]
        self.assertAlmostEqual(measurement["signedCenterline"]["width"], response["targetSpan"])
        self.assertAlmostEqual(measurement["signedCenterline"]["height"], response["targetHeight"])
        self.assertEqual(measurement["signedStrokeWidthRange"], [0, 25])
        self.assertEqual([knot["width"] for knot in measurement["resolvedAnchorWidths"]], [25, 2, 0, 2, 4.5])

    def test_rejects_invalid_handle_and_stale_offer(self):
        for handle in ("", "@a", "a-b", "é", "a" * 16):
            with self.subTest(handle=handle), self.assertRaises(ValueError):
                prepare_glyph(handle)
        other_glyph = prepare_glyph("Aa0_9")["glyph"]["sha256"]
        with self.assertRaises(ValueError):
            render_signature(MIXED_HANDLE, self.response(), glyph_sha256=other_glyph)

    def test_round_brush_uses_full_signed_width_range(self):
        glyph_hash = prepare_glyph(MIXED_HANDLE)["glyph"]["sha256"]
        response = self.response(weightAtAnchors=[{"anchor": 1, "width": 25}, {"anchor": 2, "width": 0}])
        result = render_signature(MIXED_HANDLE, response, glyph_sha256=glyph_hash)
        self.assertEqual(result["measurement"]["signedStrokeWidthRange"], [0, 25])

    def test_rejects_invalid_signing_controls(self):
        glyph_hash = prepare_glyph(MIXED_HANDLE)["glyph"]["sha256"]
        invalid_controls = {
            "negative width": {"weightAtAnchors": [{"anchor": 1, "width": -0.01}]},
            "width above maximum": {"weightAtAnchors": [{"anchor": 1, "width": 25.01}]},
            "Boolean width": {"weightAtAnchors": [{"anchor": 1, "width": True}]},
            "non-finite width": {"weightAtAnchors": [{"anchor": 1, "width": float("nan")}]},
            "duplicate anchor": {"weightAtAnchors": [{"anchor": 1, "width": 1}, {"anchor": 1, "width": 2}]},
            "gap count": {"gapShares": [100]},
            "gap total": {"gapShares": [10, 20, 30, 30]},
            "digit handle length": {"digitHandleLength": 8.01},
            "digit x movement": {"anchorMoves": [{"anchor": 3, "dx": 1, "dy": 0}]},
            "unknown field": {"digitWidth": 16},
        }
        for case, control in invalid_controls.items():
            with self.subTest(case=case), self.assertRaises(ValueError):
                render_signature(MIXED_HANDLE, self.response(**control), glyph_sha256=glyph_hash)

    def test_rejects_invalid_citations(self):
        glyph_hash = prepare_glyph(MIXED_HANDLE)["glyph"]["sha256"]
        for references in (
            ["profile"],
            ["unsigned-glyph", "unoffered"],
            ["unsigned-glyph", "profile", "profile"],
        ):
            with self.subTest(references=references), self.assertRaises(ValueError):
                render_signature(
                    MIXED_HANDLE, self.response(referencesUsed=references),
                    glyph_sha256=glyph_hash, reference_ids=("profile",),
                )

    def test_dot_uses_default_or_explicit_pressure(self):
        offer = prepare_glyph("Q")
        self.assertEqual(len(offer["anchors"]), 1)
        for entries, width in (([], 1), ([{"anchor": 1, "width": 0}], 0), ([{"anchor": 1, "width": 25}], 25)):
            with self.subTest(width=width):
                result = render_signature(
                    "Q", self.response(targetSpan=None, targetHeight=None, weightAtAnchors=entries),
                    glyph_sha256=offer["glyph"]["sha256"],
                )
                measurement = result["measurement"]
                self.assertIsNone(measurement["signedCenterline"])
                self.assertEqual(measurement["signedStrokeWidthRange"], [width, width])
                self.assertEqual(measurement["resolvedAnchorWidths"][0]["width"], width)
                svg = ElementTree.fromstring(result["signedGlyph"]["svg"])
                self.assertEqual(float(svg.find(SVG_NAMESPACE + "circle").get("r")), width / 2)
        with self.assertRaises(ValueError):
            render_signature("Q", self.response(), glyph_sha256=offer["glyph"]["sha256"])

    def test_level_handle_stays_level_after_fit(self):
        offer = prepare_glyph("000")
        self.assertEqual(offer["unsignedDimensions"]["height"], 0)
        result = render_signature("000", self.response(), glyph_sha256=offer["glyph"]["sha256"])
        measurement = result["measurement"]
        self.assertEqual(measurement["signedCenterline"]["height"], 0)
        self.assertAlmostEqual(measurement["signedCenterline"]["width"], 0.62)
        self.assertEqual(measurement["signedStrokeWidthRange"], [1, 1])

    def assert_svg(self, artifact, expected_hash):
        self.assertEqual(artifact["mediaType"], "image/svg+xml")
        self.assertEqual(artifact["sha256"], expected_hash)
        self.assertEqual(hashlib.sha256(artifact["svg"].encode("utf-8")).hexdigest(), expected_hash)
        self.assertEqual(ElementTree.fromstring(artifact["svg"]).get("viewBox"), "0 0 420 420")


if __name__ == "__main__":
    unittest.main()
