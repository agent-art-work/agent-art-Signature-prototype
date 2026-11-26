"""Pure geometry and SVG rendering for Signatures Point Version."""

import bisect
import hashlib
import html
import math
import re


CANVAS_SIZE = 420
PITCH = 20
SPAN_LIMITS = (0.35, 0.80)
HEIGHT_LIMITS = (0.10, 0.42)
GLYPH_WIDTH = 1.5
SIGN_WIDTH_LIMITS = (0, 25)
SIGN_DEFAULT_WIDTH = 1
DEFAULT_DIGIT_HANDLE_LENGTH = 6
INK = "#171c18"
PAPER = "#f4eddd"
SAMPLES_PER_CURVE = 64


def unit(character, label):
    payload = f"signatures-3-study-001:{character}:{label}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / 2**64


def _point(character, x, y, angle, incoming, outgoing, role):
    return {
        "character": character, "x": x, "y": y, "angle": angle,
        "incoming": incoming, "outgoing": outgoing, "width": GLYPH_WIDTH, "role": role,
    }


def _folded_letter(character, x):
    y = 210 + (unit(character, "height") - 0.5) * 44
    angle = math.radians(-100 + 170 * unit(character, "angle"))
    incoming = 24 + 29 * unit(character, "incoming")
    outgoing = 24 + 29 * unit(character, "outgoing")
    reach = incoming + outgoing
    if reach > 64:
        factor = 64 / reach
        incoming *= factor
        outgoing *= factor
    return _point(character, x, 210 + (y - 210) * 30 / 44, angle, incoming, outgoing, "letter")


def legacy_glyph_geometry(handle):
    """Recreate the archived multi-anchor digits and underscore bridges."""
    if not isinstance(handle, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,15}", handle):
        raise ValueError(f"Unsupported handle: {handle!r}")
    # Keep the original arithmetic order for stable archived SVG rounding.
    source_pitch = 296 / len(handle)
    scale = PITCH / source_pitch
    points = []
    for position, character in enumerate(handle):
        source_left = 62 + position * source_pitch
        source_center = source_left + source_pitch / 2
        if character.isdigit():
            reach = source_pitch * 0.15 * scale
            peak = 238 - 62 * int(character) / 9
            for source_x, y, role in (
                (source_center - 0.40 * source_pitch, 238, "pulse-start"),
                (source_center, peak, "pulse-top"),
                (source_center + 0.40 * source_pitch, 238, "pulse-end"),
            ):
                x = 210 + (source_x - 210) * scale
                points.append(_point(character, x, y, 0, reach, reach, role))
        elif character == "_":
            reach = source_pitch * 0.22 * scale
            for source_x, role in (
                (source_center - 0.40 * source_pitch, "bridge-start"),
                (source_center + 0.40 * source_pitch, "bridge-end"),
            ):
                x = 210 + (source_x - 210) * scale
                points.append(_point(character, x, 246, 0, reach, reach, role))
        else:
            x = 210 + (source_center - 210) * scale
            points.append(_folded_letter(character, x))
    return points


def glyph_geometry(handle):
    """Recreate the active glyph with one anchor per handle character."""
    points = []
    for point in legacy_glyph_geometry(handle):
        role = point["role"]
        if role == "pulse-top":
            reach = DEFAULT_DIGIT_HANDLE_LENGTH
            point.update(role="digit", incoming=reach, outgoing=reach)
        elif role == "bridge-start":
            point.update(role="underscore", x=point["x"] + 8)
        elif role != "letter":
            continue
        points.append(point)
    return points


def offered_anchors(handle, points):
    """Return the active constraints and rounded geometry for each offered anchor."""
    first_cell = 210 - PITCH * len(handle) / 2
    anchors = []
    for index, point in enumerate(points, 1):
        character = point["character"]
        letter = point["role"] == "letter"
        dx = 5 if letter else 0 if character.isdigit() else 1.4
        dy = 28 if letter else 2.5
        anchor = {
            "anchor": index,
            "characterPosition": int((point["x"] - first_cell) / PITCH) + 1,
            "character": character,
            "role": point["role"],
            "x": round(point["x"], 3),
            "y": round(point["y"], 3),
            "tangentDegrees": round(math.degrees(point["angle"]), 3),
            "incomingLength": round(point["incoming"], 3),
            "outgoingLength": round(point["outgoing"], 3),
            "dxRange": [-dx, dx],
            "dyRange": [-dy, dy],
            "turnEligible": letter and 1 < index < len(points),
        }
        if character.isupper():
            anchor["artistWeightCue"] = "emphasize"
        elif character == "_":
            anchor["artistWeightCue"] = "very-light"
        anchors.append(anchor)
    return anchors


def controls(a, b):
    return [
        (a["x"], a["y"]),
        (a["x"] + math.cos(a["angle"]) * a["outgoing"], a["y"] + math.sin(a["angle"]) * a["outgoing"]),
        (b["x"] - math.cos(b["angle"]) * b["incoming"], b["y"] - math.sin(b["angle"]) * b["incoming"]),
        (b["x"], b["y"]),
    ]


def sample(curve, t):
    u = 1 - t
    a, b, c, d = curve
    point = [
        u**3 * a[axis] + 3 * u * u * t * b[axis] + 3 * u * t * t * c[axis] + t**3 * d[axis]
        for axis in range(2)
    ]
    derivative = [
        3 * u * u * (b[axis] - a[axis]) + 6 * u * t * (c[axis] - b[axis]) + 3 * t * t * (d[axis] - c[axis])
        for axis in range(2)
    ]
    return point, derivative


def mark(points):
    if len(points) == 1:
        point = points[0]
        return f'<circle cx="{point["x"]:.3f}" cy="{point["y"]:.3f}" r="{point["width"]/2:.3f}" fill="{INK}"/>'
    left, right = [], []
    for index, (a, b) in enumerate(zip(points, points[1:])):
        curve = controls(a, b)
        for step in range(96 + (index == len(points) - 2)):
            t = step / 96
            point, derivative = sample(curve, t)
            length = math.hypot(*derivative) or 1
            ease = t * t * (3 - 2 * t)
            width = a["width"] * (1 - ease) + b["width"] * ease
            nx, ny = -derivative[1] / length, derivative[0] / length
            left.append((point[0] + nx * width / 2, point[1] + ny * width / 2))
            right.append((point[0] - nx * width / 2, point[1] - ny * width / 2))
    polygon = left + right[::-1]
    assert all(math.isfinite(value) and 10 < value < 410 for point in polygon for value in point)
    data = "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in polygon) + " Z"
    return f'<path d="{data}" fill="{INK}"/>'


def specimen(handle, points):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 420 420">'
        '<rect width="420" height="420" fill="#f4eddd"/>'
        f'{mark(points)}<text x="210" y="378" text-anchor="middle" font-size="12" '
        'font-family="Helvetica,Arial,sans-serif" fill="#34392f">'
        f'@{html.escape(handle)}</text></svg>\n'
    )


def cubic_value(values, t):
    a, b, c, d = values
    u = 1 - t
    return u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d


def x_bounds(curves):
    """Include the interior roots of each cubic's horizontal derivative."""
    extrema = []
    for curve in curves:
        x = [point[0] for point in curve]
        a = -x[0] + 3 * x[1] - 3 * x[2] + x[3]
        b = 2 * (x[0] - 2 * x[1] + x[2])
        c = x[1] - x[0]
        if abs(a) < 1e-12:
            roots = [-c / b] if abs(b) >= 1e-12 else []
        else:
            discriminant = b * b - 4 * a * c
            roots = [] if discriminant < 0 else [
                (-b + math.sqrt(discriminant)) / (2 * a),
                (-b - math.sqrt(discriminant)) / (2 * a),
            ]
        extrema.extend((x[0], x[3]))
        extrema.extend(cubic_value(x, t) for t in roots if 0 < t < 1)
    return min(extrema), max(extrema)


def checked_number(value, limits, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not limits[0] <= value <= limits[1]:
        raise ValueError(f"{label} must be within {limits}.")
    return value


def width_function(profile, *, width_limits=SIGN_WIDTH_LIMITS):
    previous_width = checked_number(profile["startWidth"], width_limits, "Start width")
    ends = []
    dimensions = []
    for segment in profile["segments"]:
        end = checked_number(segment["end"], (0, 1), "Segment progress")
        if end <= (ends[-1] if ends else 0):
            raise ValueError("Width segment progress must strictly increase.")
        control_a, control_b = [checked_number(v, width_limits, "Control width") for v in segment["controlWidths"]]
        end_width = checked_number(segment["endWidth"], width_limits, "End width")
        dimensions.append((previous_width, control_a, control_b, end_width))
        ends.append(end)
        previous_width = end_width
    if not ends or ends[-1] != 1:
        raise ValueError("The final width segment must end at progress 1.")

    def width_at(progress):
        index = bisect.bisect_left(ends, progress)
        start = ends[index - 1] if index else 0
        return cubic_value(dimensions[index], (progress - start) / (ends[index] - start))

    return width_at


def centerline_samples(curves, *, anchor_indices=None):
    points = [tuple(curves[0][0])]
    traveled = [0.0]
    if anchor_indices is not None:
        anchor_indices.append(0)
    for curve in curves:
        for step in range(1, SAMPLES_PER_CURVE + 1):
            point = tuple(sample(curve, step / SAMPLES_PER_CURVE)[0])
            distance = math.dist(points[-1], point)
            if distance > 1e-9:
                points.append(point)
                traveled.append(traveled[-1] + distance)
        if anchor_indices is not None:
            anchor_indices.append(len(points) - 1)
    return points, [distance / traveled[-1] for distance in traveled]


def anchor_widths(
    control, offered, geometry, requested, progress, anchor_indices, *,
    width_limits=SIGN_WIDTH_LIMITS, default_width=SIGN_DEFAULT_WIDTH,
):
    """Resolve offered point indices into exact sampled widths on the scaled curve."""
    if control is None or control.get("widthRange") != list(width_limits) or control.get("defaultWidth") != default_width:
        raise ValueError("Anchor width controls must declare the supported width range and default.")
    if not isinstance(offered, list) or len(offered) != len(geometry):
        raise ValueError("Expected an offered anchor for each glyph point.")

    for number, (anchor, point) in enumerate(zip(offered, geometry), 1):
        if (
            type(anchor.get("anchor")) is not int or anchor["anchor"] != number
            or anchor.get("character") != point["character"] or anchor.get("role") != point["role"]
            or any(not math.isclose(anchor[axis], point[axis], rel_tol=0, abs_tol=0.005000001) for axis in ("x", "y"))
        ):
            raise ValueError(f"Offered anchor {number} does not match the glyph point.")

    if not isinstance(requested, list):
        raise ValueError("Anchor widths must be a list.")
    assigned = {}
    for entry in requested:
        number = entry["anchor"]
        if type(number) is not int or not 1 <= number <= len(offered) or number in assigned:
            raise ValueError(f"Invalid or duplicate anchor: {number!r}.")
        assigned[number] = checked_number(entry["width"], width_limits, f"Width at anchor {number}")

    knots = [
        {
            "anchor": anchor["anchor"],
            "character": anchor["character"],
            "role": anchor["role"],
            "progress": progress[index],
            "width": assigned.get(anchor["anchor"], default_width),
        }
        for anchor, index in zip(offered, anchor_indices)
    ]
    # Repeating each endpoint width in the cubic gives a smooth, monotone transition.
    profile = {
        "startWidth": knots[0]["width"],
        "segments": [
            {"end": end["progress"], "controlWidths": [start["width"], end["width"]], "endWidth": end["width"]}
            for start, end in zip(knots, knots[1:])
        ],
    }
    width_at = width_function(profile, width_limits=width_limits)
    widths = [width_at(position) for position in progress]
    for knot, index in zip(knots, anchor_indices):
        if widths[index] != knot["width"]:
            raise ValueError(f"Sampled width differs from the requested width at anchor {knot['anchor']}.")
    for start, end in zip(anchor_indices, anchor_indices[1:]):
        low, high = sorted((widths[start], widths[end]))
        if any(not low - 1e-12 <= width <= high + 1e-12 for width in widths[start:end + 1]):
            raise ValueError("A width transition exceeds the range of its anchor widths.")
    return widths, knots


def xy(pair):
    return f"{pair[0]:.3f},{pair[1]:.3f}"


def polar(center, radius, angle):
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def cubic_line(a, b):
    controls_and_end = [tuple(x + (y - x) * t for x, y in zip(a, b)) for t in (1 / 3, 2 / 3, 1)]
    return "C" + " ".join(xy(point) for point in controls_and_end)


def circular_cubics(center, radius, start, sweep):
    count = math.ceil(sweep / (math.pi / 2))
    step = sweep / count
    control_radius = 4 / 3 * math.tan(step / 4) * radius
    commands = []
    for i in range(count):
        a = start + i * step
        b = a + step
        p = polar(center, radius, a)
        q = polar(center, radius, b)
        c1 = p[0] - control_radius * math.sin(a), p[1] + control_radius * math.cos(a)
        c2 = q[0] + control_radius * math.sin(b), q[1] - control_radius * math.cos(b)
        commands.append("C" + " ".join(xy(point) for point in (c1, c2, q)))
    return "".join(commands)


def brush_interval(a, b, radius_a, radius_b):
    """Envelope of a round brush moving between two neighboring samples."""
    distance = math.dist(a, b)
    difference = radius_b - radius_a
    if abs(difference) >= distance:
        center, radius = (b, radius_b) if radius_b >= radius_a else (a, radius_a)
        return "M" + xy(polar(center, radius, 0)) + circular_cubics(center, radius, 0, math.tau) + "Z"

    direction = math.atan2(b[1] - a[1], b[0] - a[0])
    normal_offset = math.acos(-difference / distance)
    first_normal, second_normal = direction - normal_offset, direction + normal_offset
    a1, a2 = polar(a, radius_a, first_normal), polar(a, radius_a, second_normal)
    b1, b2 = polar(b, radius_b, first_normal), polar(b, radius_b, second_normal)
    return (
        "M" + xy(a1) + cubic_line(a1, b1)
        + circular_cubics(b, radius_b, first_normal, 2 * normal_offset)
        + cubic_line(b2, a2) + circular_cubics(a, radius_a, second_normal, math.tau - 2 * normal_offset) + "Z"
    )


def filled_mark(points, widths):
    radii = [width / 2 for width in widths]
    path = "".join(
        brush_interval(a, b, radius_a, radius_b)
        for a, b, radius_a, radius_b in zip(points, points[1:], radii, radii[1:])
        if radius_a > 0 or radius_b > 0
    )
    if not path:
        return ""
    # Equal winding makes the local envelopes union through crossings and cusps.
    return f'<path d="{path}" fill="{INK}" fill-rule="nonzero"/>'


def canvas_content(handle, shape):
    return (
        f'<rect width="420" height="420" fill="{PAPER}"/>{shape}'
        f'<text x="210" y="378" text-anchor="middle" font-size="13" '
        f'font-family="Helvetica,Arial,sans-serif" fill="#34392f">@{html.escape(handle)}</text>'
    )


def curve_extrema(curves):
    left, right = x_bounds(curves)
    top, bottom = x_bounds([[(y, x) for x, y in curve] for curve in curves])
    return left, right, top, bottom


def describe_extents(curves):
    left, right, top, bottom = curve_extrema(curves)
    return {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
        "width": (right - left) / CANVAS_SIZE,
        "height": (bottom - top) / CANVAS_SIZE,
    }


def fit_dimensions(curves, target_span, target_height):
    left, right, top, bottom = curve_extrema(curves)
    if right - left < 1e-9 or (target_height and bottom - top < 1e-9):
        raise ValueError("A centerline needs nonzero width and height to fit both dimensions.")
    center_x, center_y = (left + right) / 2, (top + bottom) / 2
    gain_x = target_span * CANVAS_SIZE / (right - left)
    gain_y = target_height * CANVAS_SIZE / (bottom - top) if target_height else 0
    canvas_center = CANVAS_SIZE / 2
    return [
        [(canvas_center + (x - center_x) * gain_x, canvas_center + (y - center_y) * gain_y) for x, y in curve]
        for curve in curves
    ]
