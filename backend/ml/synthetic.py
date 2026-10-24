"""synthetic.py -- seeded, reproducible fake world for training/evaluating the matcher.

WHAT IS GENERATED
  * 14 topics that map onto 12 hidden "skills" (aliases like "DP" and
    "Dynamic Programming" share ONE skill) grouped in 4 families
    (algorithms, systems, ML, web).
  * People (seekers and group members) with hidden true ability per skill.
    What the app sees is a NOISY rating (+-0.6 sd, rounded to 1..5) on 6-10 topics.
  * Weekly free slots from 3 schedule archetypes (weekday evening / weekday
    afternoon / weekend) plus a few random slots. 15% of declared slots are not
    really free ("true slots").
  * Groups of 1-4 members (max 5 total, so they have a free seat).

HIDDEN LABEL RULE ("is this a good match for this user?")
  Uses the TRUE abilities and TRUE slots, which the model never sees.
    cap[s]   group capacity on skill s = max over members of
             max(ability[s], 0.5 * best ability in the same family)   (knowledge transfer)
    need     = mean over the user's 2 WEAKEST skills of clip((cap - ability) / 4, 0, 1)
    give     = mean over the user's 2 STRONGEST skills of clip((ability - cap) / 3, 0, 1)
    su       = 1 - exp(-true_overlap_hours / 3)                       (saturating schedule value)
    logit    = -5.0 + (8.0*need + 3.0*give) * (0.35 + 0.65*su)        (content only helps if you can meet)
               + 1.6*su + size_term - 1.2*[true_overlap < 2] + N(0, 0.4)
    label    ~ Bernoulli(sigmoid(logit))

WHY THIS IS NOT CIRCULAR (and its limits)
  1. Labels come from latent truth; the model/heuristic see noisy ratings and
     declared slots, so even the true rule cannot be recovered exactly.
  2. The rule's functional form differs from the heuristic and from the features:
     saturation, a content x schedule interaction, a size effect, family
     transfer, a hard penalty, and per-pair noise plus Bernoulli sampling.
  3. Skills the user did not rate still affect the label (the app can't see them).
  4. Evaluation splits by user AND by group, and reports an oracle that sees the
     latent truth as the ceiling.
  Limits: it is still a world I invented. It shows the pipeline works and which
  ideas help under stated assumptions; it does not prove real students will like
  the matches. Log "join"/"dismiss" clicks in the demo and retrain on those.
"""
from __future__ import annotations

import numpy as np

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# (topic_id, name, hidden skill index)
TOPICS = [
    (0, "Dynamic Programming", 0), (1, "DP", 0),
    (2, "Graph Algorithms", 1), (3, "Graphs", 1),
    (4, "NP-Completeness", 2), (5, "Greedy & Divide and Conquer", 3),
    (6, "Systems & Concurrency", 4), (7, "Operating Systems", 5), (8, "Computer Networks", 6),
    (9, "Machine Learning Basics", 7), (10, "Deep Learning", 8), (11, "Natural Language Processing", 9),
    (12, "Web Development", 10), (13, "Databases & SQL", 11),
]
TOPIC_NAMES = {t: n for t, n, _ in TOPICS}
TOPIC_SKILL = {t: s for t, _, s in TOPICS}
N_SKILLS = 12
SKILL_FAMILY = [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3]
_FAMILY_SKILLS = [[s for s in range(N_SKILLS) if SKILL_FAMILY[s] == f] for f in range(4)]
TRANSFER = 0.5

ARCHETYPES = ["evening", "afternoon", "weekend"]
_ARCH_SLOTS = {
    "evening": [(DAYS[d], h) for d in range(5) for h in range(18, 23)],
    "afternoon": [(DAYS[d], h) for d in range(5) for h in range(13, 18)],
    "weekend": [(DAYS[d], h) for d in (5, 6) for h in range(10, 18)],
}


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + np.exp(-z))


# ------------------------------------------------------------------ people
def _make_person(rng, archetype: str | None = None, boost_family: int | None = None) -> dict:
    home = int(rng.integers(0, 4))
    ability = rng.normal(2.8, 1.0, N_SKILLS)
    ability[_FAMILY_SKILLS[home]] += 1.0           # everyone has a home family
    if boost_family is not None:
        ability[_FAMILY_SKILLS[boost_family]] += 0.7
    ability = np.clip(ability, 1.0, 5.0)

    k = int(rng.integers(6, 11))
    topic_ids = sorted(int(t) for t in rng.choice(len(TOPICS), size=k, replace=False))
    ratings = {t: int(np.clip(np.rint(ability[TOPIC_SKILL[t]] + rng.normal(0, 0.6)), 1, 5))
               for t in topic_ids}

    arch = archetype or ARCHETYPES[int(rng.integers(0, 3))]
    slots = {s for s in _ARCH_SLOTS[arch] if rng.random() < 0.6}
    for _ in range(4):
        slots.add((DAYS[int(rng.integers(0, 7))], int(rng.integers(8, 23))))
    true_slots = {s for s in sorted(slots) if rng.random() < 0.85}
    return {"ability": ability, "ratings": ratings, "slots": slots, "true_slots": true_slots}


def _make_group(rng, gid: int) -> tuple[dict, dict]:
    n = int(rng.choice([1, 2, 3, 4], p=[0.1, 0.3, 0.35, 0.25]))
    home_arch = ARCHETYPES[int(rng.integers(0, 3))]
    focus = int(rng.integers(0, 4)) if rng.random() < 0.6 else None
    members, member_slots, abil, true_slots = {}, [], [], []
    for i in range(n):
        arch = home_arch if rng.random() < 0.7 else None
        p = _make_person(rng, arch, focus)
        members[f"g{gid}-m{i}"] = p["ratings"]
        member_slots.append(p["slots"])
        abil.append(p["ability"])
        true_slots.append(p["true_slots"])
    group = {"id": gid, "name": f"Group {gid}", "members": members, "member_slots": member_slots}
    latent = {"abilities": abil, "true_slots": true_slots}
    return group, latent


# ------------------------------------------------------------ hidden rule
def _capacity(abilities: list) -> np.ndarray:
    eff = []
    for a in abilities:
        e = a.copy()
        for s in range(N_SKILLS):
            others = [a[o] for o in _FAMILY_SKILLS[SKILL_FAMILY[s]] if o != s]
            e[s] = max(a[s], TRANSFER * max(others))
        eff.append(e)
    return np.max(eff, axis=0)


def true_logit(user: dict, latent: dict) -> float:
    """Noise-free log-odds that this is a good match (the oracle's view)."""
    a = user["ability"]
    cap = _capacity(latent["abilities"])

    order = np.argsort(a)                      # skill indices, weakest first
    weakest, strongest = order[:2], order[-2:]
    need = float(np.clip((cap[weakest] - a[weakest]) / 4.0, 0, 1).mean())
    give = float(np.clip((a[strongest] - cap[strongest]) / 3.0, 0, 1).mean())

    ts = latent["true_slots"]
    n = len(ts)
    ov = sum(1 for s in user["true_slots"] if 2 * sum(1 for m in ts if s in m) >= n)
    su = 1 - np.exp(-ov / 3.0)
    size_term = 0.4 * (min(n, 3) - 1) / 2.0
    return float(-5.0 + (8.0 * need + 3.0 * give) * (0.35 + 0.65 * su)
                 + 1.6 * su + size_term - 1.2 * (ov < 2))


def ideal_similarity():
    """UPPER BOUND ONLY: a similarity matrix built from the generator's own hidden
    structure (alias = 0.95, same family = 0.6). A real embedding model does not
    know this; it only sees names. Used to show how much idea (a) could add at best."""
    from ml.topic_similarity import TopicSimilarity

    ids = [t for t, _, _ in TOPICS]
    m = np.eye(len(ids))
    for i, a in enumerate(ids):
        for j, b in enumerate(ids):
            if i == j:
                continue
            sa, sb = TOPIC_SKILL[a], TOPIC_SKILL[b]
            m[i, j] = 0.95 if sa == sb else (0.6 if SKILL_FAMILY[sa] == SKILL_FAMILY[sb] else 0.0)
    return TopicSimilarity(ids, m, backend="ideal-oracle")


# ------------------------------------------------------------------ cases
def make_cases(seed: int = 0, n_users: int = 1600, n_groups: int = 400,
               list_size: int = 20, train_frac: float = 0.75):
    """Returns (train_cases, test_cases). A case is one user with `list_size`
    candidate groups:
        {"user_id", "user_ratings", "user_slots", "groups", "labels", "oracle"}
    Users AND groups are split, so test users never meet train groups."""
    rng = np.random.default_rng(seed)
    groups = [_make_group(rng, g) for g in range(n_groups)]
    users = [_make_person(rng) for _ in range(n_users)]

    g_cut = int(train_frac * n_groups)
    u_cut = int(train_frac * n_users)
    pools = {"train": groups[:g_cut], "test": groups[g_cut:]}
    seekers = {"train": list(range(u_cut)), "test": list(range(u_cut, n_users))}

    out = {}
    for split in ("train", "test"):
        cases = []
        pool = pools[split]
        for uid in seekers[split]:
            u = users[uid]
            idx = rng.choice(len(pool), size=min(list_size, len(pool)), replace=False)
            cand = [pool[int(i)] for i in idx]
            oracle = [true_logit(u, lat) for _, lat in cand]
            noisy = [z + rng.normal(0, 0.4) for z in oracle]
            labels = [int(rng.random() < _sigmoid(z)) for z in noisy]
            cases.append({
                "user_id": uid,
                "user_ratings": dict(u["ratings"]),
                "user_slots": set(u["slots"]),
                "groups": [g for g, _ in cand],
                "labels": labels,
                "oracle": oracle,
            })
        out[split] = cases
    return out["train"], out["test"]