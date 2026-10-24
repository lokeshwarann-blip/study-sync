"""Unit tests -- hand-made dicts only, no training data, no downloads.

Run from the project root:  pytest -q
"""
import time

import numpy as np
import pytest

from ml import matching
from ml.matching import FEATURE_NAMES, build_features, group_best, overlap_hours
from ml.topic_similarity import TopicSimilarity, build_topic_similarity

IDENT = TopicSimilarity.identity()
CONTRACT_KEYS = {"group_id", "match_score", "weak_topic_id", "strong_topic_id",
                 "overlap_hours", "why_matched"}


def slots(n, day="Mon", start=18):
    return {(day, start + i) for i in range(n)}


def feat(x, name):
    return x[FEATURE_NAMES.index(name)]


class StubModel:
    """predict_proba = schedule feature only, so we can tell model path from heuristic."""
    def predict_proba(self, X):
        p = X[:, FEATURE_NAMES.index("sched")]
        return np.column_stack([1 - p, p])


class BrokenModel:
    def predict_proba(self, X):
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def clean_state():
    saved = (matching._SIM, matching._NAMES, matching._MODEL, matching._MODEL_LOADED)
    matching._SIM, matching._NAMES = IDENT, {}
    matching.set_model(None)  # default: heuristic path, never touches disk
    yield
    matching._SIM, matching._NAMES, matching._MODEL, matching._MODEL_LOADED = saved


# ------------------------------------------------------------- building blocks
def test_group_best_takes_max_over_members():
    members = {"a": {1: 2, 2: 5}, "b": {1: 4}, "c": {}}
    assert group_best(members) == {1: 4, 2: 5}


def test_overlap_counts_slot_when_at_least_half_group_free():
    A, B, C, D = ("Mon", 9), ("Mon", 10), ("Mon", 11), ("Mon", 12)
    member_slots = [{A, B}, {A}, {A}, {C}]            # 4 members
    assert overlap_hours({A, B, C, D}, member_slots) == 1   # only A (3/4 free); B,C are 1/4
    assert overlap_hours({A}, [{A}, {A}, set(), set()]) == 1  # exactly half counts
    assert overlap_hours({A}, [{A}, set(), set()]) == 0       # 1 of 3 is less than half


def test_overlap_edge_cases():
    assert overlap_hours({("Mon", 9)}, []) == 0
    assert overlap_hours(set(), [{("Mon", 9)}]) == 0


# ------------------------------------------------------------------ heuristic
def test_heuristic_perfect_match_scores_100():
    g = {"id": "g", "members": {"a": {1: 5, 2: 3}}, "member_slots": [slots(8)]}
    out = matching.rank_groups_heuristic({1: 2, 2: 5}, slots(8), [g])
    assert out[0]["match_score"] == 100.0
    assert out[0]["overlap_hours"] == 8


def test_heuristic_partial_hand_computed():
    # weak topic 1 (rated 2): group best 4 -> h_in = (4-2)/(5-2) = 2/3 ; no strong topics -> h_out = 0
    # skill = 100*(0.5*2/3) = 33.33 ; overlap 4 -> schedule 50 ; final = 0.6*33.33 + 0.4*50 = 40
    g = {"id": "g", "members": {"a": {1: 4}}, "member_slots": [slots(4)]}
    out = matching.rank_groups_heuristic({1: 2}, slots(4), [g])
    assert out[0]["match_score"] == pytest.approx(40.0, abs=0.05)


def test_no_weak_or_strong_topics_does_not_divide_by_zero():
    g = {"id": "g", "members": {"a": {1: 3}}, "member_slots": [slots(2)]}
    out = matching.rank_groups_heuristic({1: 3}, slots(2), [g])   # rated 3 = neither weak nor strong
    assert out[0]["weak_topic_id"] is None and out[0]["strong_topic_id"] is None
    assert 0 <= out[0]["match_score"] <= 100


# ------------------------------------------------------------------- features
def test_hard_features_match_hand_computation():
    g = {"id": "g", "members": {"a": {1: 5, 2: 3}}, "member_slots": [slots(4)]}
    x, facts = build_features({1: 2, 2: 5}, slots(4), g, IDENT)
    assert feat(x, "h_in_hard") == pytest.approx(1.0)
    assert feat(x, "h_out_hard") == pytest.approx(1.0)
    assert feat(x, "sched") == pytest.approx(0.5)
    assert feat(x, "enough_overlap") == 1.0
    assert feat(x, "size") == pytest.approx(0.2)
    assert facts["overlap"] == 4


def test_soft_matching_gives_discounted_credit_only_above_threshold():
    g = {"id": "g", "members": {"a": {2: 5}}, "member_slots": [slots(1)]}   # group knows topic 2 only
    related = TopicSimilarity([1, 2], [[1, 0.8], [0.8, 1]])
    x, facts = build_features({1: 2}, slots(1), g, related)
    assert feat(x, "h_in_hard") == 0.0                                      # exact-topic view: no help
    assert feat(x, "h_in_soft") == pytest.approx((0.8 * 5 - 2) / 3)         # related topic: 4.0 vs 2
    item = facts["weak_items"][0]
    assert item["source"] == 2 and item["sim"] == 0.8 and item["source_rating"] == 5

    weakly_related = TopicSimilarity([1, 2], [[1, 0.5], [0.5, 1]])           # below SIM_MIN
    x2, facts2 = build_features({1: 2}, slots(1), g, weakly_related)
    assert feat(x2, "h_in_soft") == 0.0 and facts2["weak_items"] == []


def test_ratings_outside_range_are_clamped():
    g = {"id": "g", "members": {"a": {1: 5}}, "member_slots": [slots(1)]}
    x, _ = build_features({1: 0}, slots(1), g, IDENT)   # 0 -> 1 (weak), not a crash
    assert feat(x, "has_weak") == 1.0


# ---------------------------------------------------------------- rank_groups
def test_contract_shape_and_sorting():
    good = {"id": "good", "members": {"a": {1: 5}}, "member_slots": [slots(8)]}
    bad = {"id": "bad", "members": {"a": {9: 1}}, "member_slots": [set()]}
    out = matching.rank_groups({1: 1}, slots(8), [bad, good])
    assert [r["group_id"] for r in out] == ["good", "bad"]
    for r in out:
        assert set(r) == CONTRACT_KEYS
        assert isinstance(r["why_matched"], str) and r["why_matched"]
    assert out[0]["weak_topic_id"] == 1
    assert out[1]["weak_topic_id"] is None


def test_empty_inputs_do_not_crash():
    assert matching.rank_groups({1: 2}, slots(2), []) == []
    empty_group = {"id": "e", "members": {}, "member_slots": []}
    out = matching.rank_groups({}, set(), [empty_group])
    assert out[0]["overlap_hours"] == 0 and out[0]["weak_topic_id"] is None


def test_deterministic():
    gs = [{"id": i, "members": {"a": {1: 3 + i % 3}}, "member_slots": [slots(i + 1)]} for i in range(6)]
    assert matching.rank_groups({1: 2}, slots(6), gs) == matching.rank_groups({1: 2}, slots(6), gs)


def test_model_path_is_used_and_heuristic_remains_available():
    user = {1: 2, 2: 5}   # weak on topic 1, strong on topic 2
    content_only = {"id": "content", "members": {"a": {1: 5, 2: 1}}, "member_slots": [set()]}      # skill 100, overlap 0
    schedule_only = {"id": "schedule", "members": {"a": {1: 1, 2: 5}}, "member_slots": [slots(8)]}  # skill 0, overlap 8
    gs = [content_only, schedule_only]
    heur = matching.rank_groups_heuristic(user, slots(8), gs)
    assert [r["group_id"] for r in heur] == ["content", "schedule"]   # 0.6*100 = 60 vs 0.4*100 = 40
    matching.set_model(StubModel())
    model = matching.rank_groups(user, slots(8), gs)
    assert model[0]["group_id"] == "schedule"            # stub scores schedule only
    assert model[0]["match_score"] == 100.0


def test_falls_back_to_heuristic_when_model_raises():
    g = [{"id": "g", "members": {"a": {1: 4}}, "member_slots": [slots(4)]}]
    expected = matching.rank_groups_heuristic({1: 2}, slots(4), g)
    matching.set_model(BrokenModel())
    assert matching.rank_groups({1: 2}, slots(4), g) == expected


def test_missing_model_file_falls_back(tmp_path):
    assert matching.reload_model(tmp_path / "nope.joblib") is None
    g = [{"id": "g", "members": {"a": {1: 4}}, "member_slots": [slots(4)]}]
    assert matching.rank_groups({1: 2}, slots(4), g)[0]["match_score"] == pytest.approx(40.0, abs=0.05)


# ----------------------------------------------------------- why_matched text
def test_why_matched_states_only_true_facts():
    matching.set_topic_names({1: "Dynamic Programming", 2: "Graph Algorithms"}, backend="identity")
    g = {"id": "g", "members": {"a": {1: 5, 2: 3}}, "member_slots": [slots(3)]}
    text = matching.rank_groups({1: 2, 2: 5}, slots(3), [g])[0]["why_matched"]
    assert "Dynamic Programming" in text and "you rated it 2" in text and "rated it 5" in text
    assert "Graph Algorithms" in text and "the group's best is 3" in text
    assert "3 shared free hours" in text


def test_why_matched_does_not_invent_a_strength_or_schedule():
    matching.set_topic_names({1: "Dynamic Programming"}, backend="identity")
    g = {"id": "g", "members": {"a": {1: 2}}, "member_slots": [set()]}   # group no better than user, never free
    r = matching.rank_groups({1: 2}, slots(3), [g])[0]
    assert "You can help" not in r["why_matched"]
    assert "Covers your weak spot" not in r["why_matched"]
    assert "No shared free hours" in r["why_matched"]
    assert r["weak_topic_id"] is None and r["strong_topic_id"] is None


def test_why_matched_mentions_related_topic_and_similarity():
    matching._NAMES = {1: "Graphs", 2: "Graph Algorithms"}
    matching._SIM = TopicSimilarity([1, 2], [[1, 0.8], [0.8, 1]])
    g = {"id": "g", "members": {"a": {2: 5}}, "member_slots": [slots(2)]}
    r = matching.rank_groups({1: 2}, slots(2), [g])[0]
    assert "related topic Graph Algorithms" in r["why_matched"] and "0.80" in r["why_matched"]
    assert r["weak_topic_id"] == 1


def test_singular_hour_wording():
    g = {"id": "g", "members": {"a": {1: 3}}, "member_slots": [slots(1)]}
    assert "Only 1 shared free hour per week" in matching.rank_groups({1: 3}, slots(1), [g])[0]["why_matched"]


# --------------------------------------------------------- topic similarity
def test_identity_and_unknown_topics():
    s = build_topic_similarity({0: "a", 1: "b"}, backend="identity")
    assert s.get(0, 0) == 1.0 and s.get(0, 1) == 0.0 and s.get(0, 99) == 0.0


def test_tfidf_ranks_related_names_higher_and_overrides_work():
    names = {0: "Graph Algorithms", 1: "Graphs", 2: "Web Development", 3: "DP", 4: "Dynamic Programming"}
    s = build_topic_similarity(names, backend="tfidf", overrides={(3, 4): 1.0})
    assert s.get(1, 0) > s.get(1, 2)
    assert s.get(3, 4) == s.get(4, 3) == 1.0


# -------------------------------------------------------------------- speed
def test_fifty_groups_under_200ms():
    matching.set_model(StubModel())
    groups = []
    for i in range(50):
        members = {f"m{j}": {t: 1 + (i + j + t) % 5 for t in range(10)} for j in range(5)}
        groups.append({"id": i, "members": members,
                       "member_slots": [slots(20, start=0 + j) for j in range(5)]})
    user = {t: 1 + t % 5 for t in range(10)}
    matching.rank_groups(user, slots(20), groups)           # warm-up
    t0 = time.perf_counter()
    out = matching.rank_groups(user, slots(20), groups)
    assert time.perf_counter() - t0 < 0.2
    assert len(out) == 50