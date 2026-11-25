"""JSON command-line interface for the Signatures algorithm."""

import argparse
import json
import sys

from . import get_definition, prepare_glyph, render_signature


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("definition", help="Print the artist's signing rules.")
    for command in ("prepare", "sign"):
        action = commands.add_parser(command)
        action.add_argument("handle")
    args = parser.parse_args()
    try:
        if args.command == "definition":
            result = get_definition()
        elif args.command == "prepare":
            result = prepare_glyph(args.handle)
        else:
            request = json.load(sys.stdin)
            required = {"glyphSha256", "response"}
            if not isinstance(request, dict) or not required <= request.keys() <= required | {"referenceIds"}:
                raise ValueError("Signing input must contain glyphSha256, response and optional referenceIds.")
            result = render_signature(
                args.handle, request["response"], glyph_sha256=request["glyphSha256"],
                reference_ids=request.get("referenceIds", ()),
            )
    except ValueError as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
