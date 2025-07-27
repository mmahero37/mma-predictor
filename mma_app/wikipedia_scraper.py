"""Utilities to scrape fighter information from Wikipedia."""
from __future__ import annotations
import datetime as dt
import re
from typing import List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup


def fetch_wiki_html(name: str) -> str:
    slug = name.replace(" ", "_")
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{slug}"
    headers = {"User-Agent": "MMA-Predictor/1.0"}
    try:
        resp = httpx.get(api_url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception:
        page_url = f"https://en.wikipedia.org/wiki/{slug}"
        resp = httpx.get(page_url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text


def parse_age(html: str) -> Optional[int]:
    soup = BeautifulSoup(html, "html.parser")
    bday = soup.find("span", {"class": "bday"})
    if not bday:
        return None
    try:
        birth_date = dt.date.fromisoformat(bday.text)
        today = dt.date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except Exception:
        return None


def parse_last_fights(html: str, limit: int = 5) -> List[Tuple[str, str, str, dt.date]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": re.compile("(?i)wikitable")})
    fights: List[Tuple[str, str, str, dt.date]] = []
    if not table:
        return fights
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all(["th", "td"])]
        if not cols or len(cols) < 5:
            continue
        result = cols[0]
        opponent = cols[2]
        method = cols[3]
        date_str = cols[5]
        try:
            date = dt.datetime.strptime(date_str, "%d %B %Y").date()
        except ValueError:
            continue
        fights.append((result, opponent, method, date))
        if len(fights) >= limit:
            break
    return fights


def categorize_method(method: str) -> Tuple[str, str]:
    m_lower = method.lower()
    if any(x in m_lower for x in ["ko", "tko"]):
        return ("ko", "")
    if "submission" in m_lower:
        return ("sub", "")
    if "decision" in m_lower:
        if "split" in m_lower:
            return ("decision", "split")
        if "majority" in m_lower:
            return ("decision", "majority")
        return ("decision", "unanimous")
    return ("", "")


def get_last_fights_and_age(name: str) -> Tuple[Optional[int], List[Tuple[str, str, str, dt.date]]]:
    html = fetch_wiki_html(name)
    age = parse_age(html)
    fights = parse_last_fights(html, limit=5)
    return age, fights
