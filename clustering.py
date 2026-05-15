# clustering.py
import numpy as np
import hdbscan
import umap

SEVERITY_WEIGHTS = {"Very Serious": 4, "Serious": 2, "Less Serious": 1, "Marine Incident": 1}


def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int = 8) -> list:
    """
    Reduce high-dimensional embeddings with UMAP, then cluster with HDBSCAN.

    UMAP compresses 1536-dim vectors to 50 dims that preserve local neighbourhood
    structure, giving HDBSCAN meaningful density gradients instead of the near-uniform
    distances that cause it to collapse everything into one giant cluster.
    """
    print(f"  UMAP: reducing {embeddings.shape[1]}-dim embeddings → 50 dims …")
    reducer = umap.UMAP(
        n_components=50,
        n_neighbors=15,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    reduced = reducer.fit_transform(embeddings)

    print(f"  HDBSCAN: clustering {len(reduced)} points (min_cluster_size={min_cluster_size}) …")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=3,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    return clusterer.fit_predict(reduced).tolist()


def select_representatives(records: list, n: int = 10) -> list:
    """
    Select up to n representative incidents from a cluster, weighted by severity.
    Higher-severity incidents appear first.
    """
    weighted = []
    for r in records:
        weight = SEVERITY_WEIGHTS.get(r.get("Occurrence_Severity", ""), 1)
        weighted.extend([r] * weight)
    # Deterministic: take first n unique by weighted order
    seen = set()
    result = []
    for r in weighted:
        rid = r.get("Occurrence_Id") or id(r)
        if rid not in seen:
            seen.add(rid)
            result.append(r)
        if len(result) >= n:
            break
    return result


def build_cluster_text(records: list) -> str:
    """
    Build a text description of a cluster for Claude synthesis.
    Includes category distribution, contributing factor types, and pattern summaries.
    """
    if not records:
        return "No records in cluster."
    categories: dict = {}
    factor_types: dict = {}
    summaries = []

    for r in records:
        a = r.get("Analysis") or {}
        cat = a.get("incident_category", "other")
        categories[cat] = categories.get(cat, 0) + 1
        for f in a.get("contributing_factors", []):
            if not isinstance(f, dict):
                continue
            ft = f.get("type", "unknown")
            factor_types[ft] = factor_types.get(ft, 0) + 1
            desc = f.get("description")
            if desc:
                summaries.append(f"  factor: {desc}")
        summary = a.get("pattern_discovery_summary")
        if summary:
            summaries.append(f"- {summary}")

    cat_summary = ", ".join(f"{k}: {v}" for k, v in
                            sorted(categories.items(), key=lambda x: -x[1]))
    factor_summary = ", ".join(f"{k}: {v}" for k, v in
                               sorted(factor_types.items(), key=lambda x: -x[1]))

    return (
        f"Incident categories: {cat_summary}\n"
        f"Contributing factor types: {factor_summary}\n"
        f"Pattern summaries:\n" + "\n".join(summaries[:20])
    )
