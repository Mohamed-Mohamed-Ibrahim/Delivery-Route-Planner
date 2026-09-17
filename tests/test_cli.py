"""Tests for CLI interface in main.py."""

import json
import pytest
from main import run


def test_cli_sample_csv(capsys) -> None:
    code = run(["data/sample_deliveries.csv"])
    assert code == 0
    captured = capsys.readouterr()
    assert "DELIVERY ROUTE DISPATCH PLAN" in captured.out
    assert "Total Vehicle Trips     : 3" in captured.out
    assert "Trip 1" in captured.out


def test_cli_missing_file(capsys) -> None:
    code = run(["data/non_existent.csv"])
    assert code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_json_export(tmp_path, capsys) -> None:
    out_file = tmp_path / "out.json"
    code = run(["data/sample_deliveries.csv", "-o", str(out_file), "-f", "json"])
    assert code == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert len(data["trips"]) == 3
    assert data["metrics"]["total_deliveries"] == 5


def test_cli_csv_export(tmp_path, capsys) -> None:
    out_file = tmp_path / "out.csv"
    code = run(["data/sample_deliveries.csv", "-o", str(out_file), "-f", "csv"])
    assert code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "Trip ID,Trip Primary Area" in content


def test_cli_verbose_flag(capsys) -> None:
    code = run(["data/sample_deliveries.csv", "-v"])
    assert code == 0
    captured = capsys.readouterr()
    assert "DETAILED TRIP MANIFEST (DROP-OFF SEQUENCE):" in captured.out
