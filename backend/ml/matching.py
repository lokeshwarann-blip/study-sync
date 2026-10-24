"""matching.py -- study-group ranking: heuristic baseline + learned scorer.

PUBLIC API (contract with the backend -- unchanged):
    rank_groups(user_ratings, user_slots, groups) -> list[dict]
Extra helpers (optional for the backend):
    set_topic_names({topic_id: "Dynamic Programming", ...})   # call once at startup
    rank_groups_heuristic(...)                                # same output, baseline scorer

Pipeline per request (50 groups ~ a few ms):
    plain dicts -> 12 numeric features per (user, group) -> model.predict_proba
    -> sort -> why_matched text built from the SAME feature facts.
If the model file is missing, stale or raises, we silently fall back to the
original heuristic (0.6*skill + 0.4*schedule).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Hashable

import numpy as np

from ml.topic_similarity import TopicSimilarity, build_topic_similarity

log = logging.getLogger(__name__)

# ----------------------------------------------------------------- constants
WEAK_MAX = 2          # rating <= 2  -> "needs help"
STRONG_MIN = 4        # rating >= 4  -> "strong"
MAX_R = 5
SIM_MIN = 0.55        # topics less similar than this get NO credit for each other
OVERLAP_CAP_H = 8     # heuristic caps schedule at 8 shared hours
MIN_OVERLAP_OK = 2    # below this, the group is flagged "hard to meet"
MODEL_PATH = Path(__file__).parent / "models" / "matcher.joblib"

FEATURE_NAMES = [
    "h_in_hard",       # heuristic "can the group help my weak topics" (exact topics only)
    "h_out_hard",      # heuristic "can I help the group" (exact topics only)
    "h_in_soft",       # same, but related topics count (embedding similarity)
    "h_out_soft",
    "sched",           # min(overlap, 8) / 8
    "enough_overlap",  # 1 if overlap >= 2 hours
    "size",            # members / 5
    "has_weak",        # user has >=1 weak topic (otherwise h_in = 0 is meaningless)
    "has_strong",
    "skill_x_sched",   # content fit * schedule fit (help is useless if you never meet)
    "top_weak_gain",   # biggest single gap the group fills for me / 4 (the topic we headline)
    "top_give",        # biggest single gap I fill for the group / 4
]

# ------------------------------------------------------------ module state
_SIM: TopicSimilarity = TopicSimilarity.identity()
_NAMES: dict[Hashable, str] = {}
_MODEL: Any = None
_MODEL_LOADED = False


def set_topic_names(names: dict[Hashable, str], backend: str = "auto",
                    overrides: dict | None = None) -> TopicSimilarity:
    """Call once at startup with {topic_id: topic_name}. Builds the similarity
    matrix and enables readable why_matched text. Optional: without it every
    topic is only similar to itself and text falls back to 'topic <id>'."""
    global _SIM, _NAMES
    _NAMES = dict(names)
    _SIM = build_topic_similarity(names, backend=backend, overrides=overrides)
    return _SIM


def set_model(model: Any) -> None:
    """Inject a model (anything with predict_proba) or None to force the heuristic.
    Used by tests and by train_eval."""
    global _MODEL, _MODEL_LOADED
    _MODEL, _MODEL_LOADED = model, True


def reload_model(path: Path = MODEL_PATH) -> Any:
    global _MODEL, _MODEL_LOADED
    _MODEL, _MODEL_LOADED = None, True
    try:
        import joblib

        if Path(path).exists():
            blob = joblib.load(path)
            if blob.get("feature_names") == FEATURE_NAMES:
                _MODEL = blob["model"]
            else:
                log.warning("matcher.joblib has stale feature list; using heuristic")
        else:
            log.info("no matcher.joblib; using heuristic")
    except Exception as exc:
        log.warning("could not load matcher model (%s); using heuristic", exc)
    return _MODEL


def _get_model() -> Any:
    if not _MODEL_LOADED:
        reload_model()
    return _MODEL


def _name(t: Hashable) -> str:
    return _NAMES.get(t, f"topic {t}")


# ------------------------------------------------------------ small helpers
def _clean_ratings(user_ratings: dict) -> dict:
    return {t: min(MAX_R, max(1, int(r))) for t, r in user_ratings.items()}


def group_best(members: dict) -> dict:
    """Group strength per topic = max rating among members who rated it."""
    best: dict = {}
    for ratings in members.values():
        for t, r in ratings.items():
            if r > best.get(t, 0):
                best[t] = r
    return best


def overlap_hours(user_slots: set, member_slots: list) -> int:
    """A (day, hour) slot counts if the user is free and >= half the group is."""
    n = len(member_slots)
    if n == 0 or not user_slots:
        return 0
    total = 0
    for slot in user_slots:
        free = sum(1 for s in member_slots if slot in s)
        if 2 * free >= n:
            total += 1
    return total


def soft_best(topic: Hashable, best: dict, sim: TopicSimilarity):
    """Group strength on `topic`, letting related topics count at a discount.

    value = max( best[topic],  sim(topic, s) * best[s]  for related s ).
    Returns (value, source_topic_or_None, similarity_used).
    """
    val = float(best.get(topic, 0))
    src = topic if val > 0 else None
    used = 1.0
    for s, r in best.items():
        if s == topic:
            continue
        k = sim.get(topic, s)
        if k >= SIM_MIN and k * r > val:
            val, src, used = k * r, s, k
    return val, src, used


# ------------------------------------------------------------- the features
def build_features(user_ratings: dict, user_slots: set, group: dict,
                   sim: TopicSimilarity) -> tuple[np.ndarray, dict]:
    """Returns (feature vector in FEATURE_NAMES order, facts dict for explanations)."""
    ratings = _clean_ratings(user_ratings)
    members = group.get("members") or {}
    best = group_best(members)
    ov = overlap_hours(user_slots, group.get("member_slots") or [])

    weak = {t: r for t, r in ratings.items() if r <= WEAK_MAX}
    strong = {t: r for t, r in ratings.items() if r >= STRONG_MIN}

    # ---- needs: how much of my weakness can this group cover? (original formula)
    in_num_hard = in_num_soft = in_den = 0.0
    weak_items = []
    for t, r in weak.items():
        in_den += MAX_R - r
        hard = best.get(t, 0)
        soft, src, k = soft_best(t, best, sim)
        in_num_hard += max(0, hard - r)
        in_num_soft += max(0.0, soft - r)
        if soft - r > 0:
            weak_items.append({"topic": t, "user": r, "group": soft, "source": src,
                               "source_rating": best.get(src), "sim": k, "gain": soft - r})
    # ---- gives: how much can I teach this group?
    out_num_hard = out_num_soft = out_den_hard = out_den_soft = 0.0
    strong_items = []
    for t, r in strong.items():
        hard = best.get(t, 0)
        soft, _, _ = soft_best(t, best, sim)
        out_num_hard += max(0, r - hard)
        out_num_soft += max(0.0, r - soft)
        out_den_hard += MAX_R - hard
        out_den_soft += MAX_R - soft
        if r - soft > 0:
            strong_items.append({"topic": t, "user": r, "group": soft, "give": r - soft})

    h_in_hard = in_num_hard / in_den if in_den > 0 else 0.0
    h_in_soft = in_num_soft / in_den if in_den > 0 else 0.0
    h_out_hard = out_num_hard / out_den_hard if out_den_hard > 0 else 0.0
    h_out_soft = out_num_soft / out_den_soft if out_den_soft > 0 else 0.0

    sched = min(ov, OVERLAP_CAP_H) / OVERLAP_CAP_H
    skill_soft = 0.5 * h_in_soft + 0.5 * h_out_soft
    top_weak = max((d["gain"] for d in weak_items), default=0.0) / 4.0
    top_give = max((d["give"] for d in strong_items), default=0.0) / 4.0
    x = np.array([
        h_in_hard, h_out_hard, h_in_soft, h_out_soft,
        sched, 1.0 if ov >= MIN_OVERLAP_OK else 0.0,
        len(members) / 5.0,
        1.0 if weak else 0.0, 1.0 if strong else 0.0,
        skill_soft * sched,
        top_weak, top_give,
    ], dtype=float)

    skill_h = 100.0 * (0.5 * h_in_hard + 0.5 * h_out_hard)
    sched_h = min(100.0, ov / OVERLAP_CAP_H * 100.0)
    facts = {
        "overlap": ov,
        "n_members": len(members),
        "weak_items": sorted(weak_items, key=lambda d: (-d["gain"], str(d["topic"]))),
        "strong_items": sorted(strong_items, key=lambda d: (-d["give"], str(d["topic"]))),
        "heuristic": 0.6 * skill_h + 0.4 * sched_h,
    }
    return x, facts


# ---------------------------------------------------------- why_matched text
def _hours(n: int) -> str:
    return f"{n} shared free hour" + ("" if n == 1 else "s")


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def explain(facts: dict) -> str:
    """Every sentence below is a direct read-out of `facts`; nothing is invented
    and nothing about model internals is claimed."""
    parts = []
    for w in facts["weak_items"][:2]:
        if w["source"] == w["topic"]:
            parts.append(f"Covers your weak spot {_name(w['topic'])}: you rated it {w['user']}, "
                         f"the group's strongest member rated it {_num(w['group'])}.")
        else:
            parts.append(f"Helps with {_name(w['topic'])} (you rated it {w['user']}) through the "
                         f"related topic {_name(w['source'])}, where the group's best is "
                         f"{w['source_rating']} (similarity {w['sim']:.2f}).")
    for s in facts["strong_items"][:1]:
        parts.append(f"You can help on {_name(s['topic'])}: you rated it {s['user']}, "
                     f"the group's best is {_num(s['group'])}.")
    if not facts["weak_items"] and not facts["strong_items"]:
        parts.append("No clear skill complementarity found on the topics you rated.")
    ov = facts["overlap"]
    if ov == 0:
        parts.append("No shared free hours yet (a slot counts when you and at least half the group are free).")
    elif ov < MIN_OVERLAP_OK:
        parts.append(f"Only {_hours(ov)} per week, so scheduling will be tight.")
    else:
        parts.append(f"{_hours(ov).capitalize()} per week (you and at least half the group are free).")
    return " ".join(parts)


# -------------------------------------------------------------------- ranking
def _rank(user_ratings: dict, user_slots: set, groups: list, use_model: bool) -> list[dict]:
    if not groups:
        return []
    rows, facts_list = [], []
    for g in groups:
        x, f = build_features(user_ratings, user_slots, g, _SIM)
        rows.append(x)
        facts_list.append(f)
    X = np.vstack(rows)

    scores = None
    model = _get_model() if use_model else None
    if model is not None:
        try:
            scores = 100.0 * np.asarray(model.predict_proba(X))[:, 1]
        except Exception as exc:
            log.warning("model scoring failed (%s); falling back to heuristic", exc)
    if scores is None:
        scores = np.array([f["heuristic"] for f in facts_list])

    out = []
    for g, f, s in zip(groups, facts_list, scores):
        out.append({
            "group_id": g["id"],
            "match_score": round(float(s), 1),
            "weak_topic_id": f["weak_items"][0]["topic"] if f["weak_items"] else None,
            "strong_topic_id": f["strong_items"][0]["topic"] if f["strong_items"] else None,
            "overlap_hours": f["overlap"],
            "why_matched": explain(f),
        })
    out.sort(key=lambda d: (-d["match_score"], str(d["group_id"])))
    return out


def rank_groups(user_ratings: dict, user_slots: set, groups: list) -> list[dict]:
    """Contract function. Best group first. weak/strong_topic_id are None when the
    group offers no real gap to fill on that side."""
    return _rank(user_ratings, user_slots, groups, use_model=True)


def rank_groups_heuristic(user_ratings: dict, user_slots: set, groups: list) -> list[dict]:
    """Baseline: identical output shape, original 0.6*skill + 0.4*schedule score."""
    return _rank(user_ratings, user_slots, groups, use_model=False)