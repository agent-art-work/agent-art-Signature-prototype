"""Prepare and render a single Signatures signing."""

import json
import math
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from .geometry import (
    INK,
    PITCH,
    anchor_widths,
    canvas_content,
    centerline_samples,
    checked_number,
    controls,
    curve_extrema,
    describe_extents,
    filled_mark,
    fit_dimensions,
    glyph_geometry,
    offered_anchors,
    specimen,
)


_DEFINITION = json.loads(Path(__file__).with_name("definition.json").read_text(encoding="utf-8"))
_CONTROLS = _DEFINITION["controls"]
_VERSION = _DEFINITION["work"]["definitionVersion"]
_SVG_TYPE = "image/svg+xml"
_GLYPH_ID = "unsigned-glyph"
_REQUIRED_FIELDS = {
    "targetSpan", "targetHeight", "anchorMoves", "turns", "weightAtAnchors",
    "statedIntention", "referencesUsed",
}
_OPTIONAL_FIELDS = {"gapShares", "digitHandleLength", "defaultWidth"}


def get_definition():
    """Return the artist's versioned signing rules and handoff text."""
    return deepcopy(_DEFINITION)


def _svg_artifact(svg):
    return {"mediaType": _SVG_TYPE, "sha256": sha256(svg.encode("utf-8")).hexdigest(), "svg": svg}


def _curves(points):
    return [controls(left, right) for left, right in zip(points, points[1:])]


def _prepare(handle):
    if not isinstance(handle, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,15}", handle):
        raise ValueError("Use a handle of 1–15 ASCII letters, digits or underscores.")
    points = glyph_geometry(handle)
    extents = describe_extents(_curves(points)) if len(points) > 1 else None
    offer = {
        "rendererVersion": _VERSION,
        "handle": handle,
        "glyph": {"id": _GLYPH_ID, **_svg_artifact(specimen(handle, points))},
        "anchors": offered_anchors(handle, points),
        "unsignedDimensions": {
            "span": round(extents["width"], 6) if extents else 0,
            "height": round(extents["height"], 6) if extents else 0,
        },
    }
    return offer, points, extents


def prepare_glyph(handle):
    """Return the exact unsigned SVG, its digest and the offered anchors."""
    return _prepare(handle)[0]


def _validate_response(response, reference_ids):
    if not isinstance(response, dict) or not _REQUIRED_FIELDS <= response.keys() <= _REQUIRED_FIELDS | _OPTIONAL_FIELDS:
        raise ValueError("The signing response must include the required fields and only offered controls.")
    intention = response["statedIntention"]
    if not isinstance(intention, str) or not 0 < len(intention.split()) < 200:
        raise ValueError("The stated intention must contain 1–199 words.")
    if isinstance(reference_ids, (str, bytes)):
        raise ValueError("Offered reference IDs must be a collection of strings.")
    try:
        offered = tuple(reference_ids)
    except TypeError as error:
        raise ValueError("Offered reference IDs must be a collection of strings.") from error
    if any(not isinstance(item, str) or not item.strip() for item in offered):
        raise ValueError("Offered reference IDs must be nonempty strings.")
    used = response["referencesUsed"]
    if (
        not isinstance(used, list) or any(not isinstance(item, str) for item in used)
        or _GLYPH_ID not in used or len(set(used)) != len(used)
        or not set(used) <= {_GLYPH_ID, *offered}
    ):
        raise ValueError("Cite the unsigned glyph and any offered references used, with no duplicate IDs.")


def _anchor_edits(entries, anchor_count, fields, label):
    if not isinstance(entries, list):
        raise ValueError(f"{label} must be a list.")
    indexed = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.keys() != fields:
            raise ValueError(f"Invalid {label.lower()} entry.")
        anchor = entry["anchor"]
        if type(anchor) is not int or not 1 <= anchor <= anchor_count or anchor in indexed:
            raise ValueError(f"Invalid or duplicate anchor {anchor!r} in {label.lower()}.")
        indexed[anchor] = entry
    return indexed


def _place_anchors(points, shares, dx):
    control = _CONTROLS["gapShares"]
    count = len(points) - 1
    if not isinstance(shares, list) or len(shares) != count:
        raise ValueError(f"Return one gap share per boundary ({count} values).")
    shares = [checked_number(share, control["range"], "Gap share") for share in shares]
    total = control["total"]
    if not math.isclose(math.fsum(shares), total, abs_tol=1e-9, rel_tol=0):
        raise ValueError(f"Gap shares must add up to {total}.")
    flexible = control["flexibleUnitsPerBoundary"] * count
    final_x = [point["x"] + dx.get(index, 0) for index, point in enumerate(points, 1)]
    translation = 0
    for point, left, right, share in zip(points[1:], final_x, final_x[1:], shares):
        clearance = max(control["minimumCenterGap"], PITCH + control["minimumAnchorClearance"] - (right - left))
        translation += clearance + flexible * share / total - PITCH
        point["x"] += translation


def _edit_curve(points, anchors, response):
    moves = _anchor_edits(response["anchorMoves"], len(anchors), {"anchor", "dx", "dy"}, "Anchor moves")
    turns = _anchor_edits(
        response["turns"], len(anchors), {"anchor", "angleOffset", "incomingGain", "outgoingGain"},
        "Turns",
    )
    turn_control = _CONTROLS["turns"]
    if len(turns) > turn_control["limit"]:
        raise ValueError(f"Use at most {turn_control['limit']} turn edits.")
    horizontal = {
        number: checked_number(edit["dx"], anchors[number - 1]["dxRange"], f"Horizontal move at anchor {number}")
        for number, edit in moves.items()
    }
    if "digitHandleLength" in response:
        digits = [point for point in points if point["role"] == "digit"]
        if not digits:
            raise ValueError("Set digitHandleLength only when the handle contains digits.")
        reach = checked_number(
            response["digitHandleLength"], _CONTROLS["digitHandleLength"]["range"], "Digit handle length",
        )
        for point in digits:
            point.update(incoming=reach, outgoing=reach)
    if "gapShares" in response:
        _place_anchors(points, response["gapShares"], horizontal)
    vertical_control = _CONTROLS["anchorMoves"]["letterVerticalTrial"]
    expanded = 0
    for number, edit in moves.items():
        anchor, point = anchors[number - 1], points[number - 1]
        dy = checked_number(edit["dy"], anchor["dyRange"], f"Vertical move at anchor {number}")
        expanded += abs(dy) > vertical_control["usualRange"][1]
        point["x"] += horizontal[number]
        point["y"] += dy
    if expanded > vertical_control["maxExpandedLetters"]:
        raise ValueError("Only one letter may use the expanded vertical range.")
    if any(left["x"] >= right["x"] for left, right in zip(points, points[1:])):
        raise ValueError("Moved anchors must stay in their original horizontal order.")

    for number, edit in turns.items():
        if not anchors[number - 1]["turnEligible"]:
            raise ValueError(f"Turn editing is unavailable at anchor {number}.")
        point = points[number - 1]
        angle = checked_number(edit["angleOffset"], turn_control["angleRange"], "Turn angle")
        point["angle"] += math.radians(angle)
        point["incoming"] *= checked_number(edit["incomingGain"], turn_control["lengthGainRange"], "Incoming gain")
        point["outgoing"] *= checked_number(edit["outgoingGain"], turn_control["lengthGainRange"], "Outgoing gain")
    return _curves(points)


def _render_dot(point, response, pressure, default_width):
    if (
        response["targetSpan"] is not None or response["targetHeight"] is not None
        or response["anchorMoves"] != [] or response["turns"] != []
        or response.get("gapShares", []) != [] or "digitHandleLength" in response
    ):
        raise ValueError("A one-anchor glyph accepts only pressure or the default dot width.")
    width = pressure[1]["width"] if pressure else default_width
    mark = (
        f'<circle cx="{point["x"]:.3f}" cy="{point["y"]:.3f}" r="{width / 2:.3f}" fill="{INK}"/>'
    )
    return mark, None, [width, width], [
        {"anchor": 1, "character": point["character"], "role": point["role"], "width": width},
    ]


def render_signature(handle, response, *, glyph_sha256, reference_ids=()):
    """Validate a signing response against its offer and return SVG and measurements."""
    offer, points, unsigned_extents = _prepare(handle)
    if glyph_sha256 != offer["glyph"]["sha256"]:
        raise ValueError("The supplied glyph digest does not match the offered unsigned glyph.")
    _validate_response(response, reference_ids)
    anchors = offer["anchors"]
    pressure = _anchor_edits(response["weightAtAnchors"], len(anchors), {"anchor", "width"}, "Anchor widths")
    width_control = _CONTROLS["weightAtAnchors"]
    limits = tuple(width_control["widthRange"])
    default = response.get("defaultWidth", width_control["defaultWidth"])
    options = width_control["defaultWidthOptions"]
    if isinstance(default, bool) or not isinstance(default, (int, float)) or default not in options:
        raise ValueError(f"Default stroke width must be one of {options}.")
    default = int(default)
    if len(anchors) == 1:
        if pressure:
            checked_number(pressure[1]["width"], limits, "Dot width")
        mark, signed_extents, width_range, knots = _render_dot(points[0], response, pressure, default)
    else:
        span = checked_number(response["targetSpan"], _CONTROLS["targetSpan"]["range"], "Target span")
        height = checked_number(response["targetHeight"], _CONTROLS["targetHeight"]["range"], "Target height")
        curves = _edit_curve([dict(point) for point in points], anchors, response)
        _, _, top, bottom = curve_extrema(curves)
        if bottom - top < 1e-9:
            height = 0
        fitted = fit_dimensions(curves, span, height)
        signed_extents = describe_extents(fitted)
        if not all(math.isclose(signed_extents[axis], size, abs_tol=1e-10, rel_tol=0)
                   for axis, size in (("width", span), ("height", height))):
            raise ValueError("The fitted centerline differs from the requested dimensions.")
        indices = []
        samples, progress = centerline_samples(fitted, anchor_indices=indices)
        widths, knots = anchor_widths(
            {**width_control, "defaultWidth": default}, anchors, points, response["weightAtAnchors"], progress, indices,
            width_limits=limits, default_width=default,
        )
        mark = filled_mark(samples, widths)
        width_range = [round(min(widths), 4), round(max(widths), 4)]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 420 420">'
        + canvas_content(handle, mark) + "</svg>\n"
    )
    return {
        "rendererVersion": _VERSION,
        "handle": handle,
        "inputGlyphSha256": glyph_sha256,
        "signedGlyph": _svg_artifact(svg),
        "measurement": {
            "unsignedCenterline": unsigned_extents,
            "signedCenterline": signed_extents,
            "signedStrokeWidthRange": width_range,
            "resolvedAnchorWidths": knots,
        },
        "statedIntention": response["statedIntention"],
        "referencesUsed": list(response["referencesUsed"]),
    }
