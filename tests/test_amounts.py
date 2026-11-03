from fractions import Fraction

import pytest

from unit_talk.parser import evaluate, parse, parse_amount, tokenize


def amount(text):
    tokens = tokenize(text)
    value, i = parse_amount(tokens, 0)
    return value, tokens[i:]


@pytest.mark.parametrize(
    "text, value",
    [
        ("7 cups", 7),
        ("2.5 cups", Fraction(5, 2)),
        (".5 cups", Fraction(1, 2)),
        ("1/3 cup", Fraction(1, 3)),
        ("1 1/2 cups", Fraction(3, 2)),
        ("a cup", 1),
        ("an hour", 1),
        ("one cup", 1),
        ("twelve inches", 12),
        ("twenty-five feet", 25),
        ("ninety nine feet", 99),
        ("a hundred meters", 100),
        ("two hundred and ten grams", 210),
        ("three thousand five hundred feet", 3500),
        ("half cup", Fraction(1, 2)),
        ("half a cup", Fraction(1, 2)),
        ("a half cup", Fraction(1, 2)),
        ("a quarter cup", Fraction(1, 4)),
        ("a quarter of a cup", Fraction(1, 4)),
        ("three quarters of a cup", Fraction(3, 4)),
        ("two thirds cup", Fraction(2, 3)),
        ("2 thirds of a cup", Fraction(2, 3)),
        ("an eighth of a teaspoon", Fraction(1, 8)),
        ("two and a half cups", Fraction(5, 2)),
        ("1 and a quarter cups", Fraction(5, 4)),
        ("minus 40 F", -40),
        ("negative two and a half C", Fraction(-5, 2)),
    ],
)
def test_amounts(text, value):
    parsed, rest = amount(text)
    assert parsed == value
    assert rest and rest[0].lower() not in ("a", "an", "of")


def test_no_amount_leaves_position_unchanged():
    assert amount("cups") == (None, ["cups"])
    assert amount("minus cups") == (None, ["minus", "cups"])


def test_mixed_number_needs_proper_fraction():
    # "2 3/2" isn't a mixed number; the second token is left for the caller.
    assert amount("2 3/2 cups") == (2, ["3/2", "cups"])


@pytest.mark.parametrize(
    "text, value, symbol",
    [
        ("how many tablespoons in a quarter cup", 4, "tbsp"),
        ("how many teaspoons in a third of a cup", 16, "tsp"),
        ("how many ounces in a pound", 16, "oz"),
        ("how many minutes in an hour and a half", 90, "min"),
        ("a cup and a half to tbsp", 24, "tbsp"),
        ("two and a half cups to ml", Fraction("591.47059125"), "ml"),
        ("five feet and eleven inches to cm", Fraction("180.34"), "cm"),
        ("convert one hundred and five km to m", 105000, "m"),
        ("minus forty F to C", -40, "°C"),
    ],
)
def test_queries_with_words(text, value, symbol):
    query = parse(text)
    assert (evaluate(query), query.target.symbol) == (value, symbol)
