"""
Fetch UFC rankings from the official website or a local fallback.
"""
import json
import os
import re
from typing import Dict, Optional, Tuple

import httpx
from bs4 import BeautifulSoup


def _scrape_rankings() -> Dict[str, Dict[str, Optional[int]]]:
    url = "https://www.ufc.com/rankings"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception:
        return {}
    soup = BeautifulSoup(response.text, "html.parser")
    rankings: Dict[str, Dict[str, Optional[int]]] = {}
    for div in soup.select("div.view-content > div.ranking-list__item"):
        weight_class = div.select_one("span[class*='weight-class']").get_text(strip=True)
        fighters = {}
        champ = div.select_one("div.champion div.views-field--name").get_text(strip=True)
        fighters[champ] = "Champion"
        for rank_li in div.select("div.views-row"):
            rank_num_text = rank_li.select_one("span.position").get_text(strip=True)
            match = re.search(r"\d+", rank_num_text)
            rank_num = int(match.group()) if match else None
            fighter_name = rank_li.select_one("span.name").get_text(strip=True)
            fighters[fighter_name] = rank_num
        rankings[weight_class] = fighters
    return rankings


def load_rankings() -> Dict[str, Dict[str, Optional[int]]]:
    data = _scrape_rankings()
    if data:
        return data
    fallback_path = os.path.join(os.path.dirname(__file__), "rankings.json")
    with open(fallback_path, "r", encoding="utf8") as f:
        return json.load(f)


def get_fighter_rank(rankings: Dict[str, Dict[str, Optional[int]]], weight_class: str, fighter: str) -> Optional[Tuple[str, Optional[int]]]:
    fighters = rankings.get(weight_class)
    if not fighters:
        return None
    for name, rank in fighters.items():
        if name.lower() == fighter.lower():
            return ("Champion", None) if rank == "Champion" else ("Rank", rank)
    return None
