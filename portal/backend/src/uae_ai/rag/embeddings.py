"""Strict free local embedding route. No external route or paid fallback."""
import math
import time
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException


def uses_retrieval_prompts(settings):
    return settings.embedding_model.rsplit("/", 1)[-1].split(":", 1)[0].lower() == "embeddinggemma"


def retrieval_inputs(question, passages, settings):
    if uses_retrieval_prompts(settings):
        return ["task: search result | query: " + question,
                *["title: " + (p["title"] or "none") + " | text: " + p["text"] for p in passages]]
    return [question, *[p["text"] for p in passages]]


def retrieval_profile(settings):
    if settings.retrieval_mode == "lexical":
        return {"name": "bm25"}
    gemma = uses_retrieval_prompts(settings)
    return {"name": "embeddinggemma-retrieval-v1" if gemma else "raw-rrf-v1",
            "embedding_model": settings.embedding_model, "min_cosine": settings.retrieval_min_cosine,
            "dense_source_heads": 2 if gemma else 0,
            "weak_score_band": .10 if gemma else 0, "min_distinct_source_margin": .02 if gemma else 0}


def validate_route(settings):
    parsed = urlparse(settings.embedding_url)
    if (settings.app_env not in {"local", "test"} or parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or parsed.path.rstrip("/") != "/v1" or not settings.embedding_model):
        raise RuntimeError("Free hybrid retrieval requires a local/test loopback HTTP /v1 endpoint and EMBEDDING_MODEL")


def vectors(texts, settings):
    validate_route(settings)
    if len(texts) > settings.retrieval_max_chunks + 1 or any(len(text) > 4000 for text in texts):
        raise HTTPException(422, "The local embedding batch exceeds its configured capacity.")
    result, dimensions = [], None
    deadline = time.monotonic() + 120
    try:
        with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
            for start in range(0, len(texts), 16):
                if time.monotonic() >= deadline:
                    raise ValueError("Embedding deadline exceeded")
                batch = texts[start:start + 16]
                response = client.post(settings.embedding_url.rstrip("/") + "/embeddings", json={"model": settings.embedding_model, "input": batch})
                response.raise_for_status()
                if len(response.content) > 8_000_000:
                    raise ValueError("Embedding response too large")
                rows = response.json()["data"]
                if len(rows) != len(batch) or sorted(row["index"] for row in rows) != list(range(len(batch))):
                    raise ValueError("Embedding count/index mismatch")
                for row in sorted(rows, key=lambda row: row["index"]):
                    vector = row["embedding"]
                    if not isinstance(vector, list) or not 2 <= len(vector) <= 4096 or any(type(x) not in {float, int} or not math.isfinite(x) for x in vector):
                        raise ValueError("Invalid vector")
                    if dimensions is not None and len(vector) != dimensions:
                        raise ValueError("Inconsistent vector dimensions")
                    dimensions = len(vector)
                    norm = math.sqrt(sum(x * x for x in vector))
                    if not math.isfinite(norm) or norm <= 0:
                        raise ValueError("Invalid norm")
                    result.append([x / norm for x in vector])
    except (httpx.HTTPError, KeyError, ValueError, TypeError, OverflowError):
        raise HTTPException(503, "The local embedding model is unavailable or returned invalid vectors. No alternate provider was used.") from None
    return result
