from fractions import Fraction

import pytest

from unit_talk import units
from unit_talk.units import UnitError, convert, get, lookup


def conv(value, source, target):
    return convert(Fraction(value), get(source), get(target))


def test_every_alias_resolves_to_its_own_unit():
    for alias, unit in units._ALIASES.items():
        assert lookup(alias) is unit, alias


@pytest.mark.parametrize("name", ["ft", "foot", "feet", "FEET", "Feet"])
def test_aliases_and_case(name):
    assert get(name).symbol == "ft"


def test_extra_whitespace_in_multiword_alias():
    assert get("fluid   ounces").symbol == "fl oz"


@pytest.mark.parametrize("name", ["c", "f", "k", "M"])
def test_single_letters_are_case_sensitive(name):
    assert lookup(name) is None


def test_unknown_unit():
    with pytest.raises(UnitError, match="unknown unit 'furlong'"):
        get("furlong")


@pytest.mark.parametrize(
    "value, source, target, expected",
    [
        (1, "in", "cm", Fraction("2.54")),
        (1, "mi", "km", Fraction("1.609344")),
        (1, "lb", "oz", 16),
        (1, "st", "lb", 14),
        (1, "cup", "tbsp", 16),
        (1, "tbsp", "tsp", 3),
        (1, "gal", "qt", 4),
        (1, "qt", "pt", 2),
        (1, "cup", "fl oz", 8),
        (2, "h", "min", 120),
        (1, "wk", "d", 7),
    ],
)
def test_exact_conversions(value, source, target, expected):
    assert conv(value, source, target) == expected


@pytest.mark.parametrize(
    "value, source, target, expected",
    [
        (100, "°C", "°F", 212),
        (32, "°F", "°C", 0),
        (-40, "°F", "°C", -40),
        (0, "K", "°C", Fraction("-273.15")),
        (0, "°F", "K", Fraction("255.3722222222222222222")),
    ],
)
def test_temperatures(value, source, target, expected):
    assert float(conv(value, source, target)) == pytest.approx(float(expected))


def test_speed():
    assert conv(36, "km/h", "m/s") == 10
    assert float(conv(60, "mph", "km/h")) == pytest.approx(96.56064)


def test_mismatched_dimensions():
    with pytest.raises(UnitError, match="can't convert mass to length"):
        conv(1, "kg", "m")


@pytest.mark.parametrize(
    "name, guess",
    [
        ("kilometrs", "kilometres"),
        ("galon", "gallon"),
        ("farenheit", "fahrenheit"),
        ("Celcius", "celsius"),
        ("c", "°C"),
    ],
)
def test_suggest_close_alias(name, guess):
    assert units.suggest(name) == guess


@pytest.mark.parametrize("name", ["furlongs", "parsecs", "xyz"])
def test_suggest_nothing_when_far_off(name):
    assert units.suggest(name) is None


def test_unknown_unit_error_includes_suggestion():
    with pytest.raises(UnitError, match=r"unknown unit 'milez'; did you mean 'mile'\?"):
        get("milez")


@pytest.mark.parametrize(
    "value, source, target, expected",
    [
        (1, "ac", "ft2", 43560),
        (1, "ha", "m2", 10000),
        (1, "mi2", "ac", 640),
        (1, "sq ft", "square inches", 144),
        (1, "km²", "ha", 100),
        (1, "B", "bit", 8),
        (1, "KiB", "B", 1024),
        (1, "GB", "MB", 1000),
        (1, "TiB", "GiB", 1024),
        (1, "bar", "kPa", 100),
        (1, "atm", "torr", 760),
        (1, "hPa", "mbar", 1),
        (1, "kWh", "MJ", Fraction("3.6")),
        (1, "kcal", "cal", 1000),
        (1, "Cal", "kJ", Fraction("4.184")),
        (1, "Wh", "J", 3600),
    ],
)
def test_new_category_conversions(value, source, target, expected):
    assert conv(value, source, target) == expected


def test_psi_and_btu():
    assert float(conv(1, "psi", "Pa")) == pytest.approx(6894.757293168)
    assert float(conv(1, "atm", "psi")) == pytest.approx(14.69594878)
    assert float(conv(1, "BTU", "kJ")) == pytest.approx(1.05505585262)
    assert float(conv(1, "eV", "J")) == pytest.approx(1.602176634e-19)


def test_cal_case_matters():
    assert get("cal").symbol == "cal"
    assert get("Cal").symbol == "kcal"
