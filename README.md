# unit-talk

A command-line unit converter that understands plain-English queries.

```console
$ unit-talk "10 km to miles"
6.2137 mi
$ unit-talk "how many tablespoons in a quarter cup"
4 tbsp
$ unit-talk "5 ft 11 in to cm"
180.34 cm
```

## Who it's for

People who live in a terminal and want a quick conversion (a recipe, a spec sheet, a
speed) without opening a browser. The parser is hand-written and rule-based. It needs
no network access and no API keys.

## Built with

Python 3.11+ with only the standard library. Tests use pytest.

## Supported units

Length, mass, volume (including cooking units), temperature, time, speed, area
(`m2`, `sq ft`, `hectares`, `acres`), data size (`bit`, `B`, decimal `kB`/`MB`/`GB`/`TB`
and binary `KiB`/`MiB`/`GiB`/`TiB`), pressure (`Pa`, `kPa`, `bar`, `atm`, `psi`,
`mmHg`, `torr`) and energy (`J`, `kJ`, `cal`, `kcal`, `Wh`, `kWh`, `BTU`, `eV`). Common
abbreviations, full names and plurals all work (`ft`, `foot`, `feet`). Food `Cal` (capital
C) means kilocalories.

## Install

```bash
git clone https://github.com/landry-some/unit-talk.git
cd unit-talk
pipx install .        # or: python3 -m pip install --user .
```

## Run

```bash
unit-talk "350 F to C"
unit-talk --precision 2 "2 liters in cups"
unit-talk             # interactive prompt; Ctrl-D to quit
printf '1 mi to km\n2 cups to ml\n' | unit-talk   # one query per line
python3 -m unit_talk "1 mi to km"                # without installing the script
```

For scripts, `--json` prints one JSON object per query (JSON Lines when reading stdin).
Errors become `{"query": ..., "error": ...}` on stdout; the exit code still reports them.

```console
$ unit-talk --json "10 km to miles"
{"query": "10 km to miles", "value": 6.2137, "unit": "mi", "text": "6.2137 mi"}
```

Queries can use digits (`2.5`, `1/3`, `1 1/2`, `1.5e-3`), words (`two`, `a quarter`,
`two and a half`) and compound amounts (`5 ft 11 in`, `an hour and a half`). A comma
is a decimal comma (`2,5 kg`) unless it separates groups of three digits (`1,500 m` is
fifteen hundred). Results too small for the chosen precision are shown in scientific
notation (`1 mm to km` gives `1e-6 km`), and temperatures below absolute zero are
rejected.

A misspelled unit gets a suggestion: `unit-talk "10 kilometrs to mi"` reports
`unknown unit 'kilometrs'; did you mean 'kilometres'?`.

Exit codes: `0` success, `1` a query couldn't be understood or converted (for piped
input: at least one line failed), `2` bad command-line usage.

## Test

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest
pytest
```

## License

MIT. See [LICENSE](LICENSE).
