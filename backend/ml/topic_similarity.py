"""topic_similarity.py -- how related are two topic NAMES?

Why this exists: a user weak in "Graphs" should still see credit for a group
strong in "Graph Algorithms". We embed the topic names once (at startup, never
per request) and keep an N x N cosine-similarity matrix. Lookup is a dict hit.

Backends
--------
"minilm" : sentence-transformers all-MiniLM-L6-v2 (CPU, ~80 MB, best quality)
"tfidf"  : character n-gram TF-IDF from scikit-learn (no download, weaker;
           catches spelling/word overlap like "Graphs" ~ "Graph Algorithms")
"identity": a topic is only similar to itself (this IS the "no embeddings"
           ablation, and the safe default if nothing else is available)
"auto"   : try minilm, then tfidf, then identity
"""
from __future__ import annotations

import logging
from typing import Hashable

import numpy as np

log = logging.getLogger(__name__)

MINILM_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class TopicSimilarity:
    """Symmetric similarity lookup. Unknown topic ids: 1.0 to themselves, else 0."""

    def __init__(self, ids: list[Hashable], matrix: np.ndarray, backend: str = "custom"):
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (len(ids), len(ids)):
            raise ValueError("matrix must be len(ids) x len(ids)")
        self.ids = list(ids)
        self.matrix = matrix
        self.backend = backend
        self._idx = {t: i for i, t in enumerate(self.ids)}

    @classmethod
    def identity(cls) -> "TopicSimilarity":
        return cls([], np.zeros((0, 0)), backend="identity")

    def get(self, a: Hashable, b: Hashable) -> float:
        if a == b:
            return 1.0
        i, j = self._idx.get(a), self._idx.get(b)
        if i is None or j is None:
            return 0.0
        return float(self.matrix[i, j])

    def top_pairs(self, n: int = 15) -> list[tuple[Hashable, Hashable, float]]:
        """Most similar distinct pairs -- print this to sanity-check the matrix
        and to choose SIM_MIN in matching.py."""
        out = []
        for i in range(len(self.ids)):
            for j in range(i + 1, len(self.ids)):
                out.append((self.ids[i], self.ids[j], float(self.matrix[i, j])))
        out.sort(key=lambda x: -x[2])
        return out[:n]


def _embed_minilm(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer  # lazy: heavy import

    model = SentenceTransformer(MINILM_NAME, device="cpu")
    return np.asarray(model.encode(texts, normalize_embeddings=True, show_progress_bar=False))


def _embed_tfidf(texts: list[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), lowercase=True)
    return vec.fit_transform(texts).toarray()  # rows are L2-normalised


def build_topic_similarity(
    names: dict[Hashable, str],
    backend: str = "auto",
    overrides: dict[tuple[Hashable, Hashable], float] | None = None,
) -> TopicSimilarity:
    """names: {topic_id: "Dynamic Programming", ...}.

    overrides: optional hand-set pairs, e.g. {(0, 1): 1.0} to declare that topic
    1 ("DP") is an alias of topic 0. Use sparingly: it is the deterministic
    escape hatch for abbreviations that embeddings may miss.
    """
    ids = sorted(names)
    texts = [names[t] for t in ids]
    if backend == "identity" or len(ids) < 2:
        return TopicSimilarity(ids, np.eye(len(ids)), backend="identity")

    order = ["minilm", "tfidf"] if backend == "auto" else [backend]
    emb, used = None, "identity"
    for b in order:
        try:
            emb = _embed_minilm(texts) if b == "minilm" else _embed_tfidf(texts)
            used = b
            break
        except Exception as exc:  # missing package, no model file, offline...
            log.warning("topic-similarity backend %r unavailable (%s)", b, exc)

    if emb is None:
        return TopicSimilarity(ids, np.eye(len(ids)), backend="identity")

    emb = emb / np.maximum(np.linalg.norm(emb, axis=1, keepdims=True), 1e-12)
    matrix = np.clip(emb @ emb.T, 0.0, 1.0)  # negative cosine = "unrelated" = 0
    np.fill_diagonal(matrix, 1.0)

    sim = TopicSimilarity(ids, matrix, backend=used)
    for (a, b), v in (overrides or {}).items():
        if a in sim._idx and b in sim._idx:
            sim.matrix[sim._idx[a], sim._idx[b]] = v
            sim.matrix[sim._idx[b], sim._idx[a]] = v
    return sim


if __name__ == "__main__":  # python -m ml.topic_similarity
    demo = {
        0: "Dynamic Programming", 1: "DP", 2: "Graph Algorithms", 3: "Graphs",
        4: "NP-Completeness", 5: "Systems & Concurrency", 6: "Operating Systems",
        7: "Machine Learning Basics", 8: "Deep Learning", 9: "Web Development",
    }
    s = build_topic_similarity(demo)
    print("backend:", s.backend)
    for a, b, v in s.top_pairs(12):
        print(f"{v:5.2f}  {demo[a]}  ~  {demo[b]}")