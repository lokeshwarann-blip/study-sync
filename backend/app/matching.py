from collections import defaultdict
from typing import Dict, List, Set, Tuple

def group_strength(group_members_ratings: Dict[int, Dict[int, int]]) -> Dict[int, int]:
    """topic_id -> best rating among members. Input: {member_id: {topic_id: rating}}"""
    best = defaultdict(int)
    for ratings in group_members_ratings.values():
        for t, r in ratings.items():
            best[t] = max(best[t], r)
    return dict(best)

def skill_score(user_ratings: Dict[int, int], best: Dict[int, int]) -> Tuple[float, float, float]:
    """
    Computes reciprocal skill score normalized by closable gap (5 - r).
    Returns (skill_score_0_to_100, h_in, h_out).
    """
    # How much the group fills your gaps (weak topics: rating <= 2)
    weak = {t: r for t, r in user_ratings.items() if r <= 2}
    gap_total = sum(5 - r for r in weak.values())
    gap_filled = sum(max(0, best.get(t, 0) - r) for t, r in weak.items())
    h_in = gap_filled / gap_total if gap_total > 0 else 0.0

    # How much you fill the group's gaps (your strong topics: rating >= 4)
    strong = {t: r for t, r in user_ratings.items() if r >= 4}
    need_total = sum(5 - best.get(t, 0) for t in strong)
    need_filled = sum(max(0, r - best.get(t, 0)) for t, r in strong.items())
    h_out = need_filled / need_total if need_total > 0 else 0.0

    # If user has only weak or only strong, let that side carry the score
    if gap_total > 0 and need_total > 0:
        total_skill = 100.0 * (0.5 * h_in + 0.5 * h_out)
    elif gap_total > 0:
        total_skill = 100.0 * h_in
    elif need_total > 0:
        total_skill = 100.0 * h_out
    else:
        total_skill = 50.0  # neutral if user has only 3s

    return total_skill, h_in, h_out

def schedule_score(user_slots: Set[Tuple[str, int]], member_slots: List[Set[Tuple[str, int]]], cap_hours: int = 8) -> Tuple[float, int]:
    """
    Counts overlapping slots where user is free and at least half the group is free.
    Returns (schedule_score_0_to_100, overlap_count).
    """
    if not member_slots or not user_slots:
        return 0.0, 0

    need = (len(member_slots) + 1) // 2  # at least half the group free
    overlap = sum(
        1 for slot in user_slots
        if sum(slot in s for s in member_slots) >= need
    )
    return min(100.0, (overlap / cap_hours) * 100.0), overlap

def final_score(skill: float, schedule: float) -> float:
    """Combines skill complementarity (60%) and schedule overlap (40%)."""
    return round(0.6 * skill + 0.4 * schedule, 1)

def generate_why_matched(
    user_ratings: Dict[int, int],
    best_ratings: Dict[int, int],
    topic_names: Dict[int, str],
    overlap_count: int,
    top_helper_name: str = ""
) -> Tuple[str, str, str]:
    """
    Returns (why_matched_text, top_weak_topic_badge, top_strong_topic_badge).
    """
    # Find most impactful weak topic filled
    weak_filled = []
    for t, r in user_ratings.items():
        if r <= 2 and best_ratings.get(t, 0) > r:
            weak_filled.append((best_ratings.get(t, 0) - r, t, r, best_ratings.get(t, 0)))
    weak_filled.sort(reverse=True)

    # Find most impactful strong topic provided
    strong_provided = []
    for t, r in user_ratings.items():
        if r >= 4 and r > best_ratings.get(t, 0):
            strong_provided.append((r - best_ratings.get(t, 0), t, r, best_ratings.get(t, 0)))
    strong_provided.sort(reverse=True)

    weak_topic_badge = ""
    strong_topic_badge = ""
    reason_parts = []

    if weak_filled:
        _, t_id, my_r, group_r = weak_filled[0]
        name = topic_names.get(t_id, f"Topic {t_id}")
        weak_topic_badge = f"Needs help: {name} ({my_r}/5)"
        helper_str = f"{top_helper_name} excels in {name} ({group_r}/5)" if top_helper_name else f"Group excels in {name} ({group_r}/5)"
        reason_parts.append(f"{helper_str} where you requested help")
    elif user_ratings:
        lowest_t = min(user_ratings, key=user_ratings.get)
        weak_topic_badge = f"Focus: {topic_names.get(lowest_t, 'Review')} ({user_ratings[lowest_t]}/5)"

    if strong_provided:
        _, t_id, my_r, group_r = strong_provided[0]
        name = topic_names.get(t_id, f"Topic {t_id}")
        strong_topic_badge = f"Excels in: {name} ({my_r}/5)"
        reason_parts.append(f"you master {name} ({my_r}/5) to mentor peers")
    elif user_ratings:
        highest_t = max(user_ratings, key=user_ratings.get)
        strong_topic_badge = f"Excels in: {topic_names.get(highest_t, 'General')} ({user_ratings[highest_t]}/5)"

    if reason_parts:
        matched_str = "Matched because: " + " + ".join(reason_parts)
    else:
        matched_str = "Matched because: Balanced learning pace and shared course syllabus"

    if overlap_count > 0:
        matched_str += f" + {overlap_count} shared free hours this week."
    else:
        matched_str += "."

    return matched_str, weak_topic_badge, strong_topic_badge
