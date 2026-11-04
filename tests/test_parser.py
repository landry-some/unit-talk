from fractions import Fraction

import pytest

from unit_talk.parser import ParseError, evaluate, parse, tokenize
from unit_talk.units import UnitError


def answer(text):
    query = parse(text)
    return evaluate(query), query.target.symbol


def test_tokenize_splits_numbers_from_units():
    assert tokenize("10km->mi?") == ["10", "km", "->", "mi"]
    assert tokenize("1,500.5 km/h to m/s") == ["1,500.5", "km/h", "to", "m/s"]
    assert tokenize("-40°F in °C") == ["-40", "°F", "in", "°C"]


@pytest.mark.parametrize(
    "text, value, symbol",
    [
        ("10 km to m", 10000, "m"),
        ("10km in m", 10000, "m"),
        ("10 km into meters", 10000, "m"),
        ("10 km as metres", 10000, "m"),
        ("10 km -> m", 10000, "m"),
        ("10 km = m", 10000, "m"),
        ("convert 2 cups to tablespoons", 32, "tbsp"),
        ("what is 3 feet in inches?", 36, "in"),
        ("What's 1/2 gallon in quarts", 2, "qt"),
        ("1,000 g to kg", 1, "kg"),
        ("2 fluid ounces to tbsp", 4, "tbsp"),
        ("-40 degrees F to degrees C", -40, "°C"),
        ("212 F in C", 100, "°C"),
    ],
)
def test_simple_queries(text, value, symbol):
    assert answer(text) == (value, symbol)


@pytest.mark.parametrize(
    "text, value, symbol",
    [
        ("1e3 m to km", 1, "km"),
        ("1.5E-3 km to m", Fraction("1.5"), "m"),
        ("2.5e+2 cm to m", Fraction("2.5"), "m"),
        (".5e1 m to cm", 500, "cm"),
        ("6.02e23 g to kg", Fraction("6.02e20"), "kg"),
        ("2,5 kg to g", 2500, "g"),
        ("0,75 l to ml", 750, "ml"),
        ("12,3456 m to cm", Fraction("1234.56"), "cm"),
        ("1,500 m to km", Fraction("1.5"), "km"),
        ("12,345.5 m to km", Fraction("12.3455"), "km"),
        ("\u221240 F to C", -40, "°C"),
        ("-273.15 C to K", 0, "K"),
    ],
)
def test_number_formats(text, value, symbol):
    assert answer(text) == (value, symbol)


def test_tokenize_number_formats():
    assert tokenize("1.5e-3km") == ["1.5e-3", "km"]
    assert tokenize("2,5 kg, 1,000 g") == ["2,5", "kg", "1,000", "g"]


@pytest.mark.parametrize("text", ["-500 C to K", "-1 K to F", "-460 F in C"])
def test_below_absolute_zero(text):
    with pytest.raises(UnitError, match="below absolute zero"):
        evaluate(parse(text))


def test_inch_unit_next_to_in_separator():
    assert answer("10 in in cm") == (Fraction("25.4"), "cm")
    assert answer("12 in to ft") == (1, "ft")
    assert answer("1 ft to in") == (12, "in")


@pytest.mark.parametrize(
    "text, value, symbol",
    [
        ("5 ft 11 in to cm", Fraction("180.34"), "cm"),
        ("1 h 30 min to minutes", 90, "min"),
        ("2 lb 8 oz in kg", Fraction("1.133980925"), "kg"),
    ],
)
def test_compound_quantities(text, value, symbol):
    assert answer(text) == (value, symbol)


@pytest.mark.parametrize(
    "text, value, symbol",
    [
        ("how many ounces in 1 pound", 16, "oz"),
        ("how many feet in mile", 5280, "ft"),
        ("How many tablespoons are in 2 cups?", 32, "tbsp"),
        ("how much ml is in 1 tsp", Fraction("4.92892159375"), "ml"),
        ("how many in are in 1 ft", 12, "in"),
    ],
)
def test_how_many_queries(text, value, symbol):
    assert answer(text) == (value, symbol)


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "empty query"),
        ("10 furlongs to m", "unknown unit 'furlongs'"),
        ("10 km to parsecs", "unknown unit 'parsecs'"),
        ("10 km", "no target unit found"),
        ("10 km to", "missing a unit"),
        ("to km", "missing an amount"),
        ("5 ft 11 to cm", "missing a unit"),
        ("5 ft 3 kg to m", "can't add length and mass"),
        ("10 C 5 F to K", "can't add temperatures"),
        ("10 km to m please", "unexpected 'please'"),
        ("1/0 m to km", "divide by zero"),
        ("how many feet", "expected 'how many"),
    ],
)
def test_parse_errors(text, message):
    with pytest.raises(ParseError, match=message):
        parse(text)


def test_misspelled_unit_gets_a_suggestion():
    with pytest.raises(ParseError, match=r"unknown unit 'kilometrs'; did you mean 'kilometres'\?"):
        parse("10 kilometrs to miles")
    with pytest.raises(ParseError, match=r"unknown unit 'galons'; did you mean 'gallons'\?"):
        parse("2 cups to galons")


def test_dimension_mismatch_on_evaluate():
    with pytest.raises(UnitError, match="can't convert mass to length"):
        evaluate(parse("3 kg to m"))
