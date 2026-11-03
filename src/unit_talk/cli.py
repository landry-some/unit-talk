"""Command-line entry point: ``unit-talk "10 km to miles"``."""

import argparse
import sys
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

from . import __version__
from .parser import ParseError, evaluate, parse
from .units import UnitError


def format_value(value: Fraction, precision: int) -> str:
    """Round to at most ``precision`` decimal places and drop trailing zeros."""
    with localcontext() as ctx:
        ctx.prec = 60
        exact = Decimal(value.numerator) / Decimal(value.denominator)
        rounded = exact.quantize(Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP)
    text = f"{rounded:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def answer(query: str, precision: int) -> str:
    parsed = parse(query)
    return f"{format_value(evaluate(parsed), precision)} {parsed.target.symbol}"


def _precision(text: str) -> int:
    value = int(text)
    if not 0 <= value <= 30:
        raise argparse.ArgumentTypeError("must be between 0 and 30")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unit-talk",
        description="Convert units from a plain-English query. "
        "With no query, read queries interactively (or one per line from stdin).",
    )
    parser.add_argument("query", nargs="*", help='e.g. "10 km to miles"')
    parser.add_argument(
        "-p", "--precision", type=_precision, default=4, metavar="N",
        help="maximum decimal places in the result (default: 4)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _run(query: str, precision: int) -> bool:
    try:
        print(answer(query, precision))
        return True
    except (ParseError, UnitError) as exc:
        print(f"unit-talk: {exc}", file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.query:
        return 0 if _run(" ".join(args.query), args.precision) else 1

    interactive = sys.stdin.isatty()
    failed = False
    while True:
        try:
            line = input("> " if interactive else "")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            break
        if line.strip() and not _run(line, args.precision):
            failed = True
    if interactive:
        print()
        return 0
    return 1 if failed else 0
