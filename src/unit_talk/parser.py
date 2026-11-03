"""Turn a plain-English query into a conversion.

Supported shapes:

    [convert | what is] <quantity> (to|in|into|as|->|=) <unit>
    how (many|much) <unit> [are|is] in <quantity>

A quantity is one or more ``<amount> <unit>`` pairs of the same dimension,
e.g. ``5 ft 11 in``.
"""

import re
from dataclasses import dataclass
from fractions import Fraction

from . import units
from .units import Unit, UnitError

_TOKEN_RE = re.compile(
    r"""
    ->
    | -?\d{1,3}(?:,\d{3})+(?:\.\d+)?   # 1,000 or 12,345.6
    | -?\d+(?:\.\d+)?(?:/\d+)?          # 10, 2.5, 1/3
    | -?\.\d+                           # .5
    | [A-Za-z°³][A-Za-z°³/0-9'’]*       # words and symbols: km, °C, km/h, m3, what's
    | \S                                # anything else, one character
    """,
    re.VERBOSE,
)
_NUMBER_RE = re.compile(r"-?(?:\d[\d,]*(?:\.\d+)?(?:/\d+)?|\.\d+)")
_IGNORED = {"?", "!", ".", ","}
_SEPARATORS = {"to", "in", "into", "as", "->", "="}
_PREFIXES = [
    ("convert",), ("what", "is"), ("what's",), ("what’s",), ("whats",), ("how", "much", "is"),
]
_LONGEST_UNIT = 4  # words in the longest multi-word alias


class ParseError(ValueError):
    """Raised when a query can't be understood."""


@dataclass(frozen=True)
class Query:
    parts: list[tuple[Fraction, Unit]]
    target: Unit


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text) if t not in _IGNORED]


def parse_amount(tokens: list[str], i: int) -> tuple[Fraction | None, int]:
    """Read an amount starting at ``tokens[i]``; return (None, i) if there isn't one."""
    if i < len(tokens) and _NUMBER_RE.fullmatch(tokens[i]):
        try:
            return Fraction(tokens[i].replace(",", "")), i + 1
        except ZeroDivisionError:
            raise ParseError(f"can't divide by zero in '{tokens[i]}'") from None
    return None, i


def _parse_unit(tokens: list[str], i: int) -> tuple[Unit, int]:
    for n in range(min(_LONGEST_UNIT, len(tokens) - i), 0, -1):
        unit = units.lookup(" ".join(tokens[i : i + n]))
        if unit is not None:
            return unit, i + n
    if i >= len(tokens):
        raise ParseError("missing a unit")
    if _NUMBER_RE.fullmatch(tokens[i]):
        raise ParseError(f"expected a unit before '{tokens[i]}'")
    raise ParseError(f"unknown unit '{tokens[i]}'")


def _parse_quantity(tokens: list[str]) -> list[tuple[Fraction, Unit]]:
    if not tokens:
        raise ParseError("missing an amount to convert")
    parts: list[tuple[Fraction, Unit]] = []
    i = 0
    while i < len(tokens):
        amount, i = parse_amount(tokens, i)
        if amount is None:
            if parts:
                raise ParseError(f"expected a number before '{tokens[i]}'")
            amount = Fraction(1)  # "how many feet in mile"
        unit, i = _parse_unit(tokens, i)
        parts.append((amount, unit))

    first = parts[0][1]
    for _, unit in parts[1:]:
        if unit.dimension != first.dimension:
            raise ParseError(f"can't add {first.dimension} and {unit.dimension}")
        if unit.dimension == "temperature":
            raise ParseError("can't add temperatures together")
    return parts


def _parse_target(tokens: list[str]) -> Unit:
    unit, i = _parse_unit(tokens, 0)
    if i < len(tokens):
        raise ParseError(f"unexpected '{tokens[i]}' after the target unit")
    return unit


def _strip_prefix(tokens: list[str]) -> list[str]:
    lowered = [t.lower() for t in tokens]
    for prefix in _PREFIXES:
        if tuple(lowered[: len(prefix)]) == prefix:
            return tokens[len(prefix) :]
    return tokens


def _parse_how_many(tokens: list[str]) -> Query:
    # tokens after "how many" / "how much": <unit> [are|is] in <quantity>
    lowered = [t.lower() for t in tokens]
    error: ParseError | None = None
    for k, word in enumerate(lowered):
        if word != "in":
            continue
        end = k
        if end > 0 and lowered[end - 1] in ("are", "is"):
            end -= 1
        try:
            return Query(_parse_quantity(tokens[k + 1 :]), _parse_target(tokens[:end]))
        except ParseError as exc:
            error = error or exc
    raise error or ParseError("expected 'how many <unit> in <amount> <unit>'")


def parse(text: str) -> Query:
    tokens = _strip_prefix(tokenize(text))
    if not tokens:
        raise ParseError("empty query")
    lowered = [t.lower() for t in tokens]
    if lowered[0] == "how" and len(lowered) > 1 and lowered[1] in ("many", "much"):
        return _parse_how_many(tokens[2:])

    # Try each separator from the right; "in" may also be the inch unit.
    error: ParseError | None = None
    for k in range(len(tokens) - 1, -1, -1):
        if lowered[k] not in _SEPARATORS:
            continue
        try:
            return Query(_parse_quantity(tokens[:k]), _parse_target(tokens[k + 1 :]))
        except ParseError as exc:
            error = error or exc
    raise error or ParseError("no target unit found; try something like '10 km to miles'")


def evaluate(query: Query) -> Fraction:
    target = query.target
    first = query.parts[0][1]
    if first.dimension != target.dimension:
        raise UnitError(f"can't convert {first.dimension} to {target.dimension}")
    if len(query.parts) == 1:
        amount, unit = query.parts[0]
        return units.convert(amount, unit, target)
    total = sum(unit.to_base(amount) for amount, unit in query.parts)
    return target.from_base(total)
