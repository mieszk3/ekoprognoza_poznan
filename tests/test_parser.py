"""Tests for the ekoprognoza HTML parser."""

from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "ekoprognoza_2026-11-09.html"

_spec = importlib.util.spec_from_file_location(
    "ekoprognoza_parser",
    ROOT / "custom_components" / "ekoprognoza_poznan" / "parser.py",
)
parser = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parser
_spec.loader.exec_module(parser)

TODAY = date(2026, 11, 9)


@pytest.fixture(scope="module")
def days():
    return parser.parse(FIXTURE.read_text(encoding="utf-8"), TODAY)


def test_three_days_in_order(days):
    assert [d.date for d in days] == [
        date(2026, 11, 9),
        date(2026, 11, 10),
        date(2026, 11, 11),
    ]
    assert [d.label for d in days] == ["DZIŚ", "JUTRO", "POJUTRZE"]


def test_values_and_statuses(days):
    assert [d.pm10 for d in days] == [74, 56, 28]
    assert [d.statuses for d in days] == [
        ("hold", "no-fire"),
        ("hold", "no-fire"),
        ("like",),
    ]
    assert [d.fire_banned for d in days] == [True, True, False]
    assert days[0].level == "orange"


def test_messages(days):
    today = days[0]
    assert any("zaprzestać spalania" in m for m in today.warnings)
    assert set(today.warnings) <= set(today.messages)
    assert len(today.messages) == 5


def test_forecast_for(days):
    assert parser.forecast_for(days, date(2026, 11, 10)).pm10 == 56
    assert parser.forecast_for(days, date(2026, 11, 12)) is None


def test_year_rollover():
    assert parser._parse_date("czwartek 1.01", date(2026, 12, 31)) == date(2027, 1, 1)
    assert parser._parse_date("środa 31.12", date(2027, 1, 1)) == date(2026, 12, 31)


def test_empty_page_raises():
    with pytest.raises(parser.ParseError):
        parser.parse("<html><body>maintenance</body></html>", TODAY)
