"""Unit registry: every supported unit, its dimension and how to reach the base unit.

Values are kept as Fractions so conversions are exact until the final rounding.
A unit converts to its dimension's base unit with ``(value + offset) * factor``;
only temperatures use a non-zero offset.
"""

from dataclasses import dataclass
from difflib import get_close_matches
from fractions import Fraction


class UnitError(ValueError):
    """Raised for unknown units or conversions between different dimensions."""


@dataclass(frozen=True)
class Unit:
    symbol: str
    dimension: str
    factor: Fraction
    offset: Fraction = Fraction(0)

    def to_base(self, value: Fraction) -> Fraction:
        return (value + self.offset) * self.factor

    def from_base(self, value: Fraction) -> Fraction:
        return value / self.factor - self.offset


# Lookup table: alias -> Unit. Filled by _add().
_ALIASES: dict[str, Unit] = {}


def _add(symbol, dimension, factor, *aliases, offset=0):
    unit = Unit(symbol, dimension, Fraction(factor), Fraction(offset))
    for alias in (symbol, *aliases):
        if alias in _ALIASES:
            raise RuntimeError(f"duplicate unit alias {alias!r}")
        _ALIASES[alias] = unit
    return unit


# Length (base: metre)
_add("mm", "length", "0.001", "millimeter", "millimeters", "millimetre", "millimetres")
_add("cm", "length", "0.01", "centimeter", "centimeters", "centimetre", "centimetres")
_add("m", "length", 1, "meter", "meters", "metre", "metres")
_add("km", "length", 1000, "kilometer", "kilometers", "kilometre", "kilometres")
_add("in", "length", "0.0254", "inch", "inches")
_add("ft", "length", "0.3048", "foot", "feet")
_add("yd", "length", "0.9144", "yard", "yards")
_add("mi", "length", "1609.344", "mile", "miles")
_add("nmi", "length", 1852, "nautical mile", "nautical miles")

# Mass (base: kilogram)
_add("mg", "mass", "0.000001", "milligram", "milligrams")
_add("g", "mass", "0.001", "gram", "grams")
_add("kg", "mass", 1, "kilo", "kilos", "kilogram", "kilograms")
_add("t", "mass", 1000, "tonne", "tonnes", "metric ton", "metric tons")
_add("oz", "mass", "0.028349523125", "ounce", "ounces")
_add("lb", "mass", "0.45359237", "lbs", "pound", "pounds")
_add("st", "mass", "6.35029318", "stone", "stones")

# Volume (base: litre). Cooking units are US customary.
_add("ml", "volume", "0.001", "mL", "milliliter", "milliliters", "millilitre", "millilitres")
_add("cl", "volume", "0.01", "cL", "centiliter", "centiliters", "centilitre", "centilitres")
_add("dl", "volume", "0.1", "dL", "deciliter", "deciliters", "decilitre", "decilitres")
_add("l", "volume", 1, "L", "liter", "liters", "litre", "litres")
_add("m3", "volume", 1000, "m³", "cubic meter", "cubic meters", "cubic metre", "cubic metres")
_add("tsp", "volume", "0.00492892159375", "teaspoon", "teaspoons")
_add("tbsp", "volume", "0.01478676478125", "tablespoon", "tablespoons")
_add("fl oz", "volume", "0.0295735295625", "floz", "fluid ounce", "fluid ounces")
_add("cup", "volume", "0.2365882365", "cups")
_add("pt", "volume", "0.473176473", "pint", "pints")
_add("qt", "volume", "0.946352946", "quart", "quarts")
_add("gal", "volume", "3.785411784", "gallon", "gallons")

# Temperature (base: kelvin)
_add("°C", "temperature", 1, "C", "°c", "celsius", "degree celsius", "degrees celsius",
     "degrees C", "degree C", "deg C", "centigrade", offset="273.15")
_add("°F", "temperature", Fraction(5, 9), "F", "°f", "fahrenheit", "degree fahrenheit",
     "degrees fahrenheit", "degrees F", "degree F", "deg F", offset="459.67")
_add("K", "temperature", 1, "kelvin", "kelvins")

# Time (base: second)
_add("ms", "time", "0.001", "millisecond", "milliseconds")
_add("s", "time", 1, "sec", "secs", "second", "seconds")
_add("min", "time", 60, "mins", "minute", "minutes")
_add("h", "time", 3600, "hr", "hrs", "hour", "hours")
_add("d", "time", 86400, "day", "days")
_add("wk", "time", 604800, "week", "weeks")
# Julian year: 365.25 days.
_add("yr", "time", 31557600, "year", "years")

# Speed (base: metre per second)
_add("m/s", "speed", 1, "meter per second", "meters per second",
     "metre per second", "metres per second")
_add("km/h", "speed", Fraction(1000, 3600), "kph", "kmh", "kilometer per hour",
     "kilometers per hour", "kilometre per hour", "kilometres per hour", "km per hour")
_add("mph", "speed", Fraction(1609344, 3600000), "mile per hour", "miles per hour")
_add("ft/s", "speed", "0.3048", "fps", "foot per second", "feet per second")
_add("kn", "speed", Fraction(1852, 3600), "knot", "knots")

_LOWER: dict[str, Unit] = {}
for _alias, _unit in _ALIASES.items():
    _LOWER.setdefault(_alias.lower(), _unit)


def lookup(name: str) -> Unit | None:
    """Find a unit by alias. Exact case wins, then a case-insensitive match.

    Single-letter symbols like ``C`` or ``F`` only match in their own case, so a
    lone ``c`` or ``f`` is not silently read as a temperature.
    """
    name = " ".join(name.split())
    if name in _ALIASES:
        return _ALIASES[name]
    if len(name) > 1:
        return _LOWER.get(name.lower())
    return None


def suggest(name: str) -> str | None:
    """Return the closest known alias to a misspelled unit name, if any is close."""
    matches = get_close_matches(name.lower(), _LOWER, n=1, cutoff=0.75)
    if not matches:
        return None
    # A lone "c" or "f" only works in its own case, so offer the real symbol.
    return matches[0] if len(matches[0]) > 1 else _LOWER[matches[0]].symbol


def unknown_unit_message(name: str) -> str:
    guess = suggest(name)
    hint = f"; did you mean '{guess}'?" if guess else ""
    return f"unknown unit '{name}'{hint}"


def get(name: str) -> Unit:
    unit = lookup(name)
    if unit is None:
        raise UnitError(unknown_unit_message(name))
    return unit


def convert(value: Fraction, source: Unit, target: Unit) -> Fraction:
    if source.dimension != target.dimension:
        raise UnitError(f"can't convert {source.dimension} to {target.dimension}")
    base = source.to_base(value)
    if source.dimension == "temperature" and base < 0:
        raise UnitError(f"{float(value):g} {source.symbol} is below absolute zero")
    return target.from_base(base)
