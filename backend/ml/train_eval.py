"""train_eval.py -- train the scorer, compare with the heuristic, run an ablation.

Run from the project root:
    python -m ml.train_eval                    # MiniLM if installed, else TF-IDF
    python -m ml.train_eval --backend tfidf --kind gbm --no-save

Compared rankers (all evaluated on UNSEEN users and UNSEEN groups):
    random        shuffled order (floor)
    heuristic     the original 0.6*skill + 0.4*schedule
    model_full    learned scorer, features with embedding-soft topic matching
    model_no_emb  ABLATION: same model, embeddings switched off (soft == hard)
    model_ideal   UPPER BOUND: same model with a similarity matrix that knows the
                  generator's hidden topic families (no real embedder can do this)
    oracle        sees hidden truth (ceiling; labels are noisy so < 1.0)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml import matching
from ml.matching import FEATURE_NAMES, build_features
from ml.synthetic import TOPIC_NAMES, ideal_similarity, make_cases
from ml.topic_similarity import TopicSimilarity, build_topic_similarity


# ------------------------------------------------------------------ features
def featurize(cases: list, sim: TopicSimilarity):
    X, y, heur, oracle, case_idx = [], [], [], [], []
    for ci, c in enumerate(cases):
        for g, label, orc in zip(c["groups"], c["labels"], c["oracle"]):
            x, facts = build_features(c["user_ratings"], c["user_slots"], g, sim)
            X.append(x)
            y.append(label)
            heur.append(facts["heuristic"])
            oracle.append(orc)
            case_idx.append(ci)
    return (np.vstack(X), np.array(y), np.array(heur), np.array(oracle), np.array(case_idx))


# ------------------------------------------------------------------- metrics
def ndcg_at_k(labels_in_rank_order: np.ndarray, k: int, all_labels: np.ndarray) -> float:
    disc = 1.0 / np.log2(np.arange(2, k + 2))
    top = labels_in_rank_order[:k]
    dcg = float((top * disc[: len(top)]).sum())
    ideal = np.sort(all_labels)[::-1][:k]
    idcg = float((ideal * disc[: len(ideal)]).sum())
    return dcg / idcg if idcg > 0 else np.nan


def per_case_metrics(scores: np.ndarray, y: np.ndarray, case_idx: np.ndarray, k_ndcg=5, k_prec=3):
    """Returns two arrays (NDCG@k, Precision@k), one value per case (nan if no positives)."""
    nd, pr = [], []
    for ci in np.unique(case_idx):
        m = case_idx == ci
        s, lab = scores[m], y[m]
        order = np.argsort(-s, kind="stable")
        ranked = lab[order]
        nd.append(ndcg_at_k(ranked, k_ndcg, lab))
        pr.append(ranked[:k_prec].mean() if lab.sum() > 0 else np.nan)
    return np.array(nd), np.array(pr)


def bootstrap_diff(a: np.ndarray, b: np.ndarray, n_boot=2000, seed=0):
    """Paired bootstrap of mean(a - b) over cases -> (mean, lo, hi) for a 95% interval."""
    ok = ~(np.isnan(a) | np.isnan(b))
    d = (a - b)[ok]
    rng = np.random.default_rng(seed)
    means = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n_boot)]
    return float(d.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# --------------------------------------------------------------------- model
def make_model(kind: str):
    if kind == "logreg":
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
    if kind == "gbm":
        return GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.08,
                                          subsample=1.0, random_state=0)
    raise ValueError(kind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--backend", default="auto", choices=["auto", "minilm", "tfidf"])
    ap.add_argument("--kind", default="logreg", choices=["logreg", "gbm"])
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    train, test = make_cases(seed=args.seed)
    sim_full = build_topic_similarity(TOPIC_NAMES, backend=args.backend)
    sim_off = TopicSimilarity.identity()
    print(f"similarity backend: {sim_full.backend}")
    print("most similar topic pairs:")
    for a, b, v in sim_full.top_pairs(8):
        print(f"   {v:4.2f}  {TOPIC_NAMES[a]}  ~  {TOPIC_NAMES[b]}")

    Xtr, ytr, _, _, _ = featurize(train, sim_full)
    Xte, yte, hte, ote, cte = featurize(test, sim_full)
    Xtr0, _, _, _, _ = featurize(train, sim_off)
    Xte0, _, _, _, _ = featurize(test, sim_off)
    sim_ideal = ideal_similarity()
    Xtr1, _, _, _, _ = featurize(train, sim_ideal)
    Xte1, _, _, _, _ = featurize(test, sim_ideal)
    print(f"train pairs {len(ytr)}, test pairs {len(yte)}, positive rate "
          f"train {ytr.mean():.2f} / test {yte.mean():.2f}")

    full = make_model(args.kind).fit(Xtr, ytr)
    ablate = make_model(args.kind).fit(Xtr0, ytr)
    p_full = full.predict_proba(Xte)[:, 1]
    p_abl = ablate.predict_proba(Xte0)[:, 1]
    p_idl = make_model(args.kind).fit(Xtr1, ytr).predict_proba(Xte1)[:, 1]
    rng = np.random.default_rng(args.seed)

    rankers = {
        "random": rng.random(len(yte)),
        "heuristic": hte,
        "model_no_emb": p_abl,
        "model_full": p_full,
        "model_ideal": p_idl,
        "oracle": ote,
    }
    res = {name: per_case_metrics(s, yte, cte) for name, s in rankers.items()}

    print(f"\nmodel kind: {args.kind}   (mean over test users with >=1 positive)")
    print(f"{'ranker':<14}{'NDCG@5':>8}{'P@3':>8}{'AUC':>8}")
    for name, (nd, pr) in res.items():
        auc = roc_auc_score(yte, rankers[name])
        print(f"{name:<14}{np.nanmean(nd):8.3f}{np.nanmean(pr):8.3f}{auc:8.3f}")

    print("\npaired bootstrap, mean difference in NDCG@5 [95% interval]:")
    for a, b in [("model_full", "heuristic"), ("model_full", "model_no_emb"),
                 ("model_ideal", "model_no_emb")]:
        m, lo, hi = bootstrap_diff(res[a][0], res[b][0])
        print(f"   {a} - {b}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    if args.kind == "logreg":
        coefs = full.named_steps["logisticregression"].coef_[0]
        print("\nstandardised LR coefficients (bigger = more influence):")
        for n, c in sorted(zip(FEATURE_NAMES, coefs), key=lambda t: -abs(t[1])):
            print(f"   {n:<16}{c:+.2f}")

    if not args.no_save:
        path = matching.MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": full, "feature_names": FEATURE_NAMES, "kind": args.kind,
                     "backend": sim_full.backend}, path)
        print(f"\nsaved model to {path}")


if __name__ == "__main__":
    main()