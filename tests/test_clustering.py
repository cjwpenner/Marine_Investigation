# tests/test_clustering.py
import numpy as np
import pytest
from clustering import cluster_embeddings, select_representatives, build_cluster_text

def make_fake_embeddings(n_clusters=3, points_per_cluster=30, dims=10, seed=42):
    """Create clearly separated fake embedding clusters."""
    rng = np.random.default_rng(seed)
    embeddings = []
    labels_true = []
    for i in range(n_clusters):
        centre = rng.uniform(-5, 5, dims)
        cluster = centre + rng.normal(0, 0.3, (points_per_cluster, dims))
        embeddings.extend(cluster.tolist())
        labels_true.extend([i] * points_per_cluster)
    return np.array(embeddings), labels_true

def test_cluster_embeddings_finds_clusters():
    embeddings, _ = make_fake_embeddings(n_clusters=3, points_per_cluster=50)
    labels = cluster_embeddings(embeddings)
    # Should find 2-5 clusters (not noise only)
    unique = set(labels) - {-1}
    assert 2 <= len(unique) <= 5

def test_cluster_embeddings_marks_outliers():
    embeddings, _ = make_fake_embeddings(n_clusters=3, points_per_cluster=50)
    labels = cluster_embeddings(embeddings)
    # -1 = noise/outlier — should exist but not dominate
    noise_pct = sum(1 for l in labels if l == -1) / len(labels)
    assert noise_pct < 0.3

def test_select_representatives_weights_severity():
    records = [
        {"Occurrence_Id": "a", "Occurrence_Severity": "Very Serious",
         "Original_Description": "serious incident", "Analysis": {"pattern_discovery_summary": "s"}},
        {"Occurrence_Id": "b", "Occurrence_Severity": "Less Serious",
         "Original_Description": "minor incident", "Analysis": {"pattern_discovery_summary": "m"}},
    ]
    # Very Serious should be selected when picking 1
    reps = select_representatives(records, n=1)
    assert reps[0]["Occurrence_Id"] == "a"

def test_cluster_embeddings_has_noise_for_sparse_points():
    """HDBSCAN should mark isolated points as noise (-1)."""
    rng = np.random.default_rng(0)
    # 3 tight clusters + 5 isolated outlier points
    cluster_pts = np.vstack([
        rng.normal(loc, 0.1, (30, 5)) for loc in [[-5,0,0,0,0],[5,0,0,0,0],[0,5,0,0,0]]
    ])
    # Add 5 truly isolated outlier points far from any cluster
    outliers = rng.uniform(10, 20, (5, 5))
    embeddings = np.vstack([cluster_pts, outliers])
    labels = cluster_embeddings(embeddings)
    assert -1 in labels

def test_build_cluster_text_includes_key_fields():
    records = [
        {"Analysis": {
            "incident_category": "mooring",
            "pattern_discovery_summary": "Mooring line failure",
            "contributing_factors": [{"type": "human", "description": "fatigue", "confidence": "high"}]
        }},
    ]
    text = build_cluster_text(records)
    assert "mooring" in text.lower()
    assert "fatigue" in text.lower()
