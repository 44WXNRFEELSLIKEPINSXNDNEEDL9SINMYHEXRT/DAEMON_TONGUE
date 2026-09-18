"""Drop near-duplicate phrases by embedding similarity.

Exact-match dedup misses rewordings — "I will drown them in oceans of blood"
and "I shall drown them in an ocean of blood" are two rows but one phrase.

Needs the optional extra: uv sync --extra dedup
"""

THRESHOLD = 0.92
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def drop_near_duplicates(
    rows: list[tuple[str, str, str]],
    threshold: float = THRESHOLD,
) -> tuple[list[tuple[str, str, str]], int]:
    """Keep the first row of each near-duplicate cluster. Returns (kept, dropped_count)."""
    try:
        import torch
        from sentence_transformers import SentenceTransformer, util
    except ImportError:
        raise SystemExit("Semantic dedup needs extras: uv sync --extra dedup") from None

    if len(rows) < 2:
        return rows, 0

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(
        [row[0] for row in rows],
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    scores = util.cos_sim(embeddings, embeddings)

    kept: list[int] = []
    for index in range(len(rows)):
        if kept and torch.max(scores[index, kept]).item() >= threshold:
            continue
        kept.append(index)

    return [rows[i] for i in kept], len(rows) - len(kept)
