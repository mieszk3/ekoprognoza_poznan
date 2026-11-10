"""Parser for the Poznań ekoprognoza page (no Home Assistant imports)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})")
_INT_RE = re.compile(r"\d+")
_STATUS_PREFIX = "status-"
_LEVEL_PREFIX = "traffic-"

STATUS_NO_FIRE = "no-fire"


class ParseError(Exception):
    """Raised when the page does not contain the expected forecast cards."""


@dataclass(frozen=True)
class DayForecast:
    """Forecast for a single day as shown on the page."""

    label: str
    date: date
    pm10: Optional[int]
    level: Optional[str]
    statuses: tuple[str, ...]
    messages: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def fire_banned(self) -> bool:
        return STATUS_NO_FIRE in self.statuses


def parse(html: str, today: date) -> list[DayForecast]:
    """Return the forecast cards ordered by date, one per day."""
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("#ekoprognoza div.jumbotron") or soup

    days: dict[date, DayForecast] = {}
    for title in root.select("h4.card-title"):
        card = title.find_parent(class_="card-block")
        if not isinstance(card, Tag):
            continue
        day = _parse_card(card, title, today)
        days.setdefault(day.date, day)

    if not days:
        raise ParseError("No forecast cards found on the page")
    return [days[d] for d in sorted(days)]


def forecast_for(days: list[DayForecast], target: date) -> Optional[DayForecast]:
    """Return the card for the given date, if the page has one."""
    return next((day for day in days if day.date == target), None)


def _parse_card(card: Tag, title: Tag, today: date) -> DayForecast:
    date_tag = title.select_one("span.date")
    if date_tag is None:
        raise ParseError("Forecast card without a date")
    day_date = _parse_date(date_tag.get_text(strip=True), today)

    label = "".join(
        str(text) for text in title.find_all(string=True, recursive=False)
    ).strip()
    label = re.sub(r"^na\s+", "", label, flags=re.IGNORECASE)

    level = next(
        (c[len(_LEVEL_PREFIX) :] for c in title.get("class", []) if c.startswith(_LEVEL_PREFIX)),
        None,
    )

    pm10 = None
    value_tag = card.select_one("text.svg-label-text:not(.small) tspan")
    if value_tag is not None:
        match = _INT_RE.search(value_tag.get_text())
        if match:
            pm10 = int(match.group())

    statuses: list[str] = []
    for tag in card.select(".eko-bottom [class]"):
        for css_class in tag.get("class", []):
            if css_class.startswith(_STATUS_PREFIX):
                status = css_class[len(_STATUS_PREFIX) :]
                if status not in statuses:
                    statuses.append(status)

    messages: list[str] = []
    warnings: list[str] = []
    for item in card.select(".komunikat li"):
        text = " ".join(item.get_text(" ", strip=True).split())
        if not text:
            continue
        messages.append(text)
        if "warning" in item.get("class", []):
            warnings.append(text)

    return DayForecast(
        label=label,
        date=day_date,
        pm10=pm10,
        level=level,
        statuses=tuple(statuses),
        messages=tuple(messages),
        warnings=tuple(warnings),
    )


def _parse_date(text: str, today: date) -> date:
    """Parse "poniedziałek 9.11" picking the year closest to today."""
    match = _DATE_RE.search(text)
    if match is None:
        raise ParseError(f"Unrecognised date: {text!r}")
    day, month = int(match.group(1)), int(match.group(2))
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(date(year, month, day))
        except ValueError:
            continue
    if not candidates:
        raise ParseError(f"Invalid date: {text!r}")
    return min(candidates, key=lambda d: abs((d - today).days))
