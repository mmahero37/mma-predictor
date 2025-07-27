from typing import List, Tuple, Optional, Dict, Union
import datetime as dt


def compute_fighter_score(
    fights: List[Tuple[str, str, str, dt.date]],
    ranking_map: Dict[str, Union[str, int, None]],
    age: Optional[int],
) -> float:
    """
    Compute the MMA Math score for a fighter given last fights, ranking map of opponents, and age.
    fights: list of tuples (result, opponent, method, date)
    ranking_map: dict mapping fighter names to rank ("Champion", integer for rank, or None)
    age: fighter's age in years
    """
    score = 0.0
    finish_streak = 0
    finish_loss_streak = 0
    for result, opponent, method, date in fights:
        opp_rank = ranking_map.get(opponent)
        m_lower = method.lower() if method else ""
        is_finish = any(x in m_lower for x in ["ko", "tko", "submission", "sub"])
        if result.lower() == "win":
            # Victory Points
            if opp_rank == "Champion":
                score += 16
            elif isinstance(opp_rank, int):
                score += max(16 - opp_rank, 0.5)
            else:
                score += 0.5
            # Finish bonus
            if is_finish:
                score += 5
                finish_streak += 1
                if finish_streak > 1:
                    score += finish_streak - 1
            else:
                finish_streak = 0
                if "split" in m_lower:
                    score -= 2
                elif "majority" in m_lower:
                    score -= 1
        else:
            # Loss Penalties
            if opp_rank == "Champion":
                score -= 2
            elif isinstance(opp_rank, int):
                if opp_rank <= 5:
                    score -= 5
                elif opp_rank <= 11:
                    score -= 7
                elif opp_rank <= 15:
                    score -= 12
                else:
                    score -= 15
            else:
                score -= 15
            if is_finish:
                score -= 5
                finish_loss_streak += 1
                if finish_loss_streak > 1:
                    score -= finish_loss_streak - 1
            else:
                finish_loss_streak = 0
                if "split" in m_lower:
                    score += 2
                elif "majority" in m_lower:
                    score += 1
    # Age penalty
    if age is not None and age > 35:
        score -= 5 + (age - 35)
    # Undefeated bonus
    if fights and all(r.lower() == "win" for r, _, _, _ in fights):
        score += 5
    # Last 5 wins bonus
    if len(fights) >= 5 and sum(1 for r, _, _, _ in fights[:5] if r.lower() == "win") == 5:
        score += 3
    return score


def predict_winner(
    name_a: str,
    data_a: Tuple[Optional[int], List[Tuple[str, str, str, dt.date]]],
    name_b: str,
    data_b: Tuple[Optional[int], List[Tuple[str, str, str, dt.date]]],
    ranking_func,
) -> Dict[str, object]:
    """
    Compare two fighters and determine the predicted winner using the MMA math model.

    data_a and data_b are tuples of (age, fights).
    ranking_func(opponent_name) -> rank ("Champion" or int or None)
    Returns a dict with scores and predicted winner.
    """
    age_a, fights_a = data_a
    age_b, fights_b = data_b

    ranking_cache: Dict[str, Union[str, int, None]] = {}

    def get_rank(name: str):
        if name not in ranking_cache:
            try:
                ranking_cache[name] = ranking_func(name)
            except Exception:
                ranking_cache[name] = None
        return ranking_cache[name]

    ranking_map_a = {opp: get_rank(opp) for _, opp, _, _ in fights_a}
    ranking_map_b = {opp: get_rank(opp) for _, opp, _, _ in fights_b}

    score_a = compute_fighter_score(fights_a, ranking_map_a, age_a)
    score_b = compute_fighter_score(fights_b, ranking_map_b, age_b)
    winner = name_a if score_a >= score_b else name_b
    return {
        "fighter_a": name_a,
        "fighter_b": name_b,
        "score_a": score_a,
        "score_b": score_b,
        "winner": winner,
    }
