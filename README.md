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

## Supported units (v0.1)

Length, mass, volume (including cooking units), temperature, time and speed. Common
abbreviations, full names and plurals all work (`ft`, `foot`, `feet`).

## Install

```bash
git clone https://github.com/<your-account>/unit-talk.git
cd unit-talk
pipx install .        # or: python3 -m pip install --user .
```

## Run

```bash
unit-talk "350 F to C"
unit-talk --precision 2 "2 liters in cups"
unit-talk             # interactive prompt; Ctrl-D to quit
```

Exit codes: `0` success, `1` the query couldn't be understood or converted, `2` bad
command-line usage.

## Test

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest
pytest
```

## License

MIT. See [LICENSE](LICENSE).
