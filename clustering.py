# clustering.py
import numpy as np
import hdbscan

SEVERITY_WEIGHTS = {"Very Serious": 4, "Serious": 2, "Less Serious": 1, "Marine Incident": 1}


def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int = 20) -> list:
    """
    Run HDBSCAN on a 2D numpy array of embeddings.
    Returns list of integer cluster labels (-1 = noise/outlier).
    """
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=5,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    return clusterer.fit_predict(embeddings).tolist()


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
        rid = r.get("Occurrence_Id")
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
    categories: dict = {}
    factor_types: dict = {}
    summaries = []

    for r in records:
        a = r.get("Analysis") or {}
        cat = a.get("incident_category", "other")
        categories[cat] = categories.get(cat, 0) + 1
        for f in a.get("contributing_factors", []):
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
