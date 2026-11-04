import io
import json
from fractions import Fraction

import pytest

from unit_talk.cli import format_value, main


@pytest.mark.parametrize(
    "value, precision, expected",
    [
        (Fraction(10000, 1609344) * 1000, 4, "6.2137"),
        (Fraction("180.34"), 4, "180.34"),
        (Fraction(4), 4, "4"),
        (Fraction(2, 3), 2, "0.67"),
        (Fraction(5, 2), 0, "3"),
        (Fraction(-1, 100000), 4, "0"),
        (Fraction(10) ** 25, 4, "10000000000000000000000000"),
    ],
)
def test_format_value(value, precision, expected):
    assert format_value(value, precision) == expected


def test_one_shot(capsys):
    assert main(["10 km to miles"]) == 0
    assert capsys.readouterr().out == "6.2137 mi\n"


def test_unquoted_words_are_joined(capsys):
    assert main(["5", "ft", "11", "in", "to", "cm"]) == 0
    assert capsys.readouterr().out == "180.34 cm\n"


def test_precision_flag(capsys):
    assert main(["--precision", "1", "2 liters in cups"]) == 0
    assert capsys.readouterr().out == "8.5 cup\n"


def test_error_exit_code(capsys):
    assert main(["3 kg to m"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "unit-talk: can't convert mass to length\n"


def test_bad_precision_is_usage_error(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["-p", "-1", "1 m to cm"])
    assert exc.value.code == 2


def test_reads_lines_from_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("1 ft to in\n\n100 C to F\n"))
    assert main([]) == 0
    assert capsys.readouterr().out == "12 in\n212 °F\n"


def test_stdin_failure_sets_exit_code_but_continues(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("1 ft to kg\n1 ft to in\n"))
    assert main([]) == 1
    captured = capsys.readouterr()
    assert captured.out == "12 in\n"
    assert "can't convert length to mass" in captured.err


def test_json_output(capsys):
    assert main(["--json", "10 km to miles"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "query": "10 km to miles", "value": 6.2137, "unit": "mi", "text": "6.2137 mi",
    }


def test_json_whole_number_is_an_int(capsys):
    assert main(["--json", "100 C to F"]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["value"] == 212 and isinstance(record["value"], int)
    assert record["unit"] == "°F"


def test_json_error_goes_to_stdout(capsys):
    assert main(["--json", "3 kg to m"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"query": "3 kg to m", "error": "can't convert mass to length"}
    assert captured.err == ""


def test_json_lines_from_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("1 ft to in\n1 ft to kg\n"))
    assert main(["--json"]) == 1
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r.get("text") for r in lines] == ["12 in", None]
    assert "error" in lines[1]
