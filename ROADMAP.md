# Roadmap

Work planned after v0.1. Estimates are rough; total is about 26 hours.

## Features

- [ ] Area, data size (KB/KiB), pressure and energy categories (3 h)
- [ ] Multiple targets in one query (`to km and miles`) and mixed-unit output (`1.8 m → 5 ft 10.9 in`) (2.5 h)
- [ ] User-defined units and aliases from a TOML config file (2 h)
- [ ] Simple arithmetic in queries (`3 cups + 2 tbsp in ml`) (3 h)
- [x] `--json` output for scripting and reading queries from stdin (1 h)
- [ ] Shell completion for unit names (bash/zsh/fish) (1.5 h)

## Bugs and edge cases

- [ ] Ambiguous units: US vs imperial gallon/pint/ton, `oz` (mass) vs `fl oz` (2 h)
- [x] Negative temperatures, scientific notation, very large or small values, locale decimal commas (1.5 h)
- [x] "Did you mean…?" suggestions for misspelled units (1.5 h)

## Refactors

- [ ] Move the unit registry from code to a data file, with a dimension-vector model for derived units (2.5 h)
- [ ] Split the parser into a tokenizer and a grammar so errors can point to positions (1.5 h)

## Tests

- [ ] Round-trip property tests with Hypothesis, plus a golden corpus of phrases (2 h)
- [ ] GitHub Actions CI across Python 3.11–3.13 (0.5 h)

## Docs

- [ ] README example list, supported-units reference generated from the registry, CHANGELOG (1.5 h)
