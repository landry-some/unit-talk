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
    | -?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!,?\d)  # 1,000 or 12,345.6
    | -?\d+,\d+                              # decimal comma: 2,5
    | -?\d+(?:\.\d+)?(?:[eE][-+]?\d+|/\d+)?   # 10, 2.5, 1/3, 1.5e-3
    | -?\.\d+(?:[eE][-+]?\d+)?                # .5, .5e3
    | [A-Za-z°²³][A-Za-z°²³/0-9'’]*          # words and symbols: km, °C, km/h, m², what's
    | \S                                     # anything else, one character
    """,
    re.VERBOSE,
)
_NUMBER_RE = re.compile(r"-?(?:\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+|/\d+)?|\.\d+(?:[eE][-+]?\d+)?)")
_THOUSANDS_RE = re.compile(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?")
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
    text = text.replace("\u2212", "-")  # Unicode minus sign
    return [t for t in _TOKEN_RE.findall(text) if t not in _IGNORED]


def _number(token: str) -> Fraction:
    """Read a numeric token; a comma is a thousands separator only in groups of three."""
    if _THOUSANDS_RE.fullmatch(token):
        return Fraction(token.replace(",", ""))
    return Fraction(token.replace(",", "."))


_SMALL = {
    w: n
    for n, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen".split()
    )
}
_TENS = {
    w: 10 * n
    for n, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split(), 2)
}
_SCALES = {"hundred": 100, "thousand": 1000}
_DENOMINATORS = {
    "half": 2, "halves": 2, "third": 3, "thirds": 3, "quarter": 4, "quarters": 4,
    "fourth": 4, "fourths": 4, "fifth": 5, "fifths": 5, "sixth": 6, "sixths": 6,
    "eighth": 8, "eighths": 8,
}
_NEGATIVES = {"minus", "negative"}


def _lower(tokens: list[str], i: int) -> str:
    return tokens[i].lower() if i < len(tokens) else ""


def _parse_digits(tokens: list[str], i: int) -> tuple[Fraction | None, int]:
    """10, 2.5, 1/3, 1,000, and mixed numbers like ``1 1/2``."""
    if not _NUMBER_RE.fullmatch(_lower(tokens, i)):
        return None, i
    try:
        value = _number(tokens[i])
        i += 1
        nxt = _lower(tokens, i)
        if value.denominator == 1 and value >= 0 and "/" in nxt and _NUMBER_RE.fullmatch(nxt):
            fraction = Fraction(nxt)
            if 0 < fraction < 1:
                value += fraction
                i += 1
    except ZeroDivisionError:
        raise ParseError(f"can't divide by zero in '{tokens[i]}'") from None
    return value, i


def _parse_words(tokens: list[str], i: int) -> tuple[Fraction | None, int]:
    """Cardinal words: "a", "seven", "twenty-five", "two hundred and ten"."""
    total = current = 0
    start = i
    if _lower(tokens, i) in ("a", "an"):
        current = 1
        i += 1
    while i < len(tokens):
        word = _lower(tokens, i)
        if word in _SMALL:
            current += _SMALL[word]
        elif word in _TENS:
            current += _TENS[word]
            if _lower(tokens, i + 1) == "-" and _SMALL.get(_lower(tokens, i + 2), 0) in range(1, 10):
                current += _SMALL[_lower(tokens, i + 2)]
                i += 2
        elif word in _SCALES:
            if word == "thousand":
                total += max(current, 1) * 1000
                current = 0
            else:
                current = max(current, 1) * 100
        elif (
            word == "and"
            and i > start
            and _lower(tokens, i - 1) in _SCALES
            and (_lower(tokens, i + 1) in _SMALL or _lower(tokens, i + 1) in _TENS)
        ):
            pass  # "one hundred and five"
        else:
            break
        i += 1
    if i == start:
        return None, i
    return Fraction(total + current), i


def _parse_and_fraction(tokens: list[str], i: int) -> tuple[Fraction | None, int]:
    """'and a half', 'and one quarter' -> (1/2, next index)."""
    if _lower(tokens, i) == "and" and _lower(tokens, i + 1) in ("a", "an", "one"):
        den = _DENOMINATORS.get(_lower(tokens, i + 2))
        if den:
            return Fraction(1, den), i + 3
    return None, i


def parse_amount(tokens: list[str], i: int) -> tuple[Fraction | None, int]:
    """Read an amount starting at ``tokens[i]``; return (None, i) if there isn't one.

    Handles digits ("2.5", "1/3", "1 1/2"), words ("two", "a", "twenty-five"),
    fractions ("half", "a quarter", "three quarters"), "two and a half", and the
    filler in "half a cup" or "a third of a cup".
    """
    start = i
    sign = 1
    if _lower(tokens, i) in _NEGATIVES:
        sign = -1
        i += 1

    value, i = _parse_digits(tokens, i)
    if value is None:
        value, i = _parse_words(tokens, i)

    den = _DENOMINATORS.get(_lower(tokens, i))
    if den:
        value = (value if value is not None else 1) / den
        i += 1
    if value is None:
        return None, start

    extra, i = _parse_and_fraction(tokens, i)
    if extra is not None:
        value += extra

    if _lower(tokens, i) == "of":
        i += 1
    if den and _lower(tokens, i) in ("a", "an"):
        i += 1
    return sign * value, i


def _parse_unit(tokens: list[str], i: int) -> tuple[Unit, int]:
    for n in range(min(_LONGEST_UNIT, len(tokens) - i), 0, -1):
        unit = units.lookup(" ".join(tokens[i : i + n]))
        if unit is not None:
            return unit, i + n
    if i >= len(tokens):
        raise ParseError("missing a unit")
    if _NUMBER_RE.fullmatch(tokens[i]):
        raise ParseError(f"expected a unit before '{tokens[i]}'")
    raise ParseError(units.unknown_unit_message(tokens[i]))


def _parse_quantity(tokens: list[str]) -> list[tuple[Fraction, Unit]]:
    if not tokens:
        raise ParseError("missing an amount to convert")
    parts: list[tuple[Fraction, Unit]] = []
    i = 0
    while i < len(tokens):
        if parts and _lower(tokens, i) == "and":
            i += 1  # "5 feet and 11 inches"
        amount, i = parse_amount(tokens, i)
        if amount is None:
            if parts:
                raise ParseError(f"expected a number before '{tokens[i]}'")
            amount = Fraction(1)  # "how many feet in mile"
        unit, i = _parse_unit(tokens, i)
        parts.append((amount, unit))
        extra, i = _parse_and_fraction(tokens, i)
        if extra is not None:
            parts.append((extra, unit))  # "a cup and a half"

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
