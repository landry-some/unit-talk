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

# Area (base: square metre)
def _area_aliases(symbol, *names):
    """m2 -> m², sq m, square meter(s)... for each long name given."""
    short = symbol[:-1]
    aliases = [f"{short}²", f"sq {short}"]
    for name in names:
        aliases += [f"square {name}", f"sq {name}"]
    return aliases


_add("mm2", "area", "0.000001", *_area_aliases("mm2", "millimeter", "millimeters",
                                                "millimetre", "millimetres"))
_add("cm2", "area", "0.0001", *_area_aliases("cm2", "centimeter", "centimeters",
                                              "centimetre", "centimetres"))
_add("m2", "area", 1, *_area_aliases("m2", "meter", "meters", "metre", "metres"))
_add("km2", "area", 1000000, *_area_aliases("km2", "kilometer", "kilometers",
                                             "kilometre", "kilometres"))
_add("ha", "area", 10000, "hectare", "hectares")
_add("in2", "area", "0.00064516", *_area_aliases("in2", "inch", "inches"))
_add("ft2", "area", "0.09290304", *_area_aliases("ft2", "foot", "feet"))
_add("yd2", "area", "0.83612736", *_area_aliases("yd2", "yard", "yards"))
_add("ac", "area", "4046.8564224", "acre", "acres")
_add("mi2", "area", "2589988.110336", *_area_aliases("mi2", "mile", "miles"))

# Data size (base: byte). kB, MB... are powers of 1000; KiB, MiB... powers of 1024.
_add("bit", "data", Fraction(1, 8), "bits")
_add("B", "data", 1, "byte", "bytes")
_add("kB", "data", 1000, "KB", "kilobyte", "kilobytes")
_add("MB", "data", 1000**2, "megabyte", "megabytes")
_add("GB", "data", 1000**3, "gigabyte", "gigabytes")
_add("TB", "data", 1000**4, "terabyte", "terabytes")
_add("KiB", "data", 1024, "kibibyte", "kibibytes")
_add("MiB", "data", 1024**2, "mebibyte", "mebibytes")
_add("GiB", "data", 1024**3, "gibibyte", "gibibytes")
_add("TiB", "data", 1024**4, "tebibyte", "tebibytes")

# Pressure (base: pascal)
_add("Pa", "pressure", 1, "pascal", "pascals")
_add("hPa", "pressure", 100, "hectopascal", "hectopascals")
_add("kPa", "pressure", 1000, "kilopascal", "kilopascals")
_add("MPa", "pressure", 1000000, "megapascal", "megapascals")
_add("mbar", "pressure", 100, "millibar", "millibars")
_add("bar", "pressure", 100000, "bars")
_add("atm", "pressure", 101325, "atmosphere", "atmospheres")
# Pound-force per square inch: 1 lb * standard gravity / (1 in)².
_add("psi", "pressure", Fraction("0.45359237") * Fraction("9.80665") / Fraction("0.0254") ** 2)
_add("mmHg", "pressure", "133.322387415", "millimeter of mercury", "millimeters of mercury")
_add("torr", "pressure", Fraction(101325, 760), "Torr")

# Energy (base: joule)
_add("J", "energy", 1, "joule", "joules")
_add("kJ", "energy", 1000, "kilojoule", "kilojoules")
_add("MJ", "energy", 1000000, "megajoule", "megajoules")
_add("cal", "energy", "4.184", "calorie", "calories")
# Food "Calories" are kilocalories.
_add("kcal", "energy", 4184, "Cal", "kilocalorie", "kilocalories")
_add("Wh", "energy", 3600, "watt hour", "watt hours")
_add("kWh", "energy", 3600000, "kilowatt hour", "kilowatt hours")
_add("BTU", "energy", "1055.05585262", "Btu", "btu", "btus", "BTUs")
_add("eV", "energy", "1.602176634e-19", "electronvolt", "electronvolts", "electron volt",
     "electron volts")

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
