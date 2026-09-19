"""Unit tests for loader module."""

import json
import pytest
from src.loader import load_deliveries, load_from_csv, load_from_json


def test_load_sample_csv(tmp_path) -> None:
    csv_path = "data/sample_deliveries.csv"
    res = load_deliveries(csv_path)
    assert len(res.deliveries) == 5
    assert len(res.rejected_items) == 0

    first = res.deliveries[0]
    assert first.id == "1" or first.id == 1
    assert first.area == "Nasr City"
    assert first.priority == 2
    assert first.weight == 4.5


def test_load_sample_json() -> None:
    json_path = "data/sample_deliveries.json"
    res = load_deliveries(json_path)
    assert len(res.deliveries) == 5
    assert len(res.rejected_items) == 0


def test_load_nonexistent_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_deliveries("data/does_not_exist.csv")


def test_load_empty_file(tmp_path) -> None:
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")
    res = load_deliveries(str(empty_csv))
    assert len(res.deliveries) == 0
    assert len(res.rejected_items) == 0

    empty_json = tmp_path / "empty.json"
    empty_json.write_text("")
    res_json = load_deliveries(str(empty_json))
    assert len(res_json.deliveries) == 0
    assert len(res_json.rejected_items) == 0


def test_load_malformed_csv_rows(tmp_path) -> None:
    bad_csv = tmp_path / "corrupt.csv"
    bad_csv.write_text(
        "ID,Area,Priority,Package Weight (kg)\n"
        "1,Maadi,1,-2.0\n"  # negative weight
        "2,Maadi,0,3.0\n"   # invalid priority 0
        "3,,1,4.0\n"        # missing area
        ",Zamalek,1,2.0\n"  # missing id
        "5,Dokki,abc,2.0\n" # non-numeric priority
        "6,Dokki,1,xyz\n"   # non-numeric weight
        "7,Nasr City,2,5.0\n" # valid
    )
    res = load_from_csv(str(bad_csv))
    assert len(res.deliveries) == 1
    assert res.deliveries[0].area == "Nasr City"
    assert len(res.rejected_items) == 6


def test_load_header_variations(tmp_path) -> None:
    custom_csv = tmp_path / "headers.csv"
    custom_csv.write_text(
        "  id  , AREA , Priority , weight \n"
        "PKG-99,Heliopolis,1,3.5\n"
        "PKG-100,Maadi,2,4.0\n"
    )
    res = load_from_csv(str(custom_csv))
    assert len(res.deliveries) == 2
    assert res.deliveries[0].id == "PKG-99"
    assert res.deliveries[0].area == "Heliopolis"
    assert res.deliveries[0].priority == 1
    assert res.deliveries[0].weight == 3.5
    assert res.deliveries[1].id == "PKG-100"
    assert res.deliveries[1].weight == 4.0



def test_load_json_invalid_structure(tmp_path) -> None:
    bad_json = tmp_path / "invalid_struct.json"
    bad_json.write_text('{"id": 1, "area": "Maadi"}')  # not an array
    with pytest.raises(ValueError, match="top-level array"):
        load_from_json(str(bad_json))
