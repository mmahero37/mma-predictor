import httpx
from typing import List, Dict, Optional, Any


def american_to_prob(american: float) -> Optional[float]:
    """Convert American odds to implied probability."""
    if american is None:
        return None
    if american > 0:
        return 100 / (american + 100)
    else:
        return -american / (-american + 100)


async def get_upcoming_fights(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch upcoming MMA fights and return averaged odds and implied probabilities.
    Uses The Odds API; set your API key via environment variable or parameter.
    Returns a list of fights with fighters, average American odds and implied probabilities.
    """
    url = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds"
    params = {
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
        "apiKey": api_key,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
        resp.raise_for_status()
        events = resp.json()

    fights = []
    for event in events:
        event_name = event.get("name")
        commence_time = event.get("commence_time")
        home = event.get("home_team")
        away = event.get("away_team")
        if not home or not away:
            continue
        odds_map: Dict[str, List[float]] = {home: [], away: []}
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name")
                        price = outcome.get("price")
                        if name in odds_map and price is not None:
                            odds_map[name].append(price)
        avg_odds: Dict[str, float] = {}
        implied: Dict[str, Optional[float]] = {}
        for fighter, prices in odds_map.items():
            if prices:
                average = sum(prices) / len(prices)
                avg_odds[fighter] = average
                implied[fighter] = american_to_prob(average)
        fights.append({
            "event": event_name,
            "commence_time": commence_time,
            "fighters": [home, away],
            "average_odds": avg_odds,
            "implied_probabilities": implied,
        })
    return fights
