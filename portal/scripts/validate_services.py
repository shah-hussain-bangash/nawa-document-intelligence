"""Live, secret-free local service evidence. This is not production acceptance."""
import argparse
from uae_ai import __version__
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import httpx
import jwt
from uae_ai.api.auth import discovery
from uae_ai.core.config import Settings
from uae_ai.rag.ocr import capabilities
from uae_ai.rag.embeddings import vectors
from uae_ai.rag.retrieval import answer_question


def validate(settings):
    settings.validate()
    checks = []
    def check(name, enabled, action):
        if not enabled:
            checks.append({"name": name, "status": "not_configured"})
            return
        try:
            detail = action()
            checks.append({"name": name, "status": "passed", "detail": detail})
        except Exception as exc:
            # Provider exceptions may include URLs, bodies or credentials. Report type only.
            checks.append({"name": name, "status": "failed", "error_type": type(exc).__name__})
    def ocr():
        value = capabilities(settings.ocr_languages)
        if not value["ready"]:
            raise RuntimeError("OCR prerequisites missing")
        return {"languages": settings.ocr_languages, "max_pages": settings.ocr_max_pages}
    def identity():
        metadata = discovery(settings)
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.get(metadata["jwks_uri"])
            response.raise_for_status()
            keys = response.json()["keys"]
        supported = [key for key in keys if key.get("use", "sig") == "sig" and key.get("alg") in {"RS256", "ES256"}]
        if not supported:
            raise ValueError("No supported identity key")
        for key in supported:
            jwt.PyJWK.from_dict(key)
        return {"discovery_and_signing_keys": True, "interactive_login_verified": False}
    def model():
        doc = SimpleNamespace(id="validation", title="Synthetic service probe", version=1, status="ready", category="Policy", classification="synthetic", pages=[{"page": 1, "text": "The synthetic service verification number is 4729."}])
        from dataclasses import replace
        result = answer_question("What is the synthetic service verification number?", [doc], replace(settings, retrieval_mode="lexical"))
        if result["mode"] == "extractive" or "4729" not in result["answer"]:
            raise ValueError("Model did not ground the probe in its source")
        return {"mode": result["mode"], "single_grounding_probe": True, "benchmark_pass": False}
    def embedding():
        values = vectors(["Synthetic procurement verification", "Synthetic procurement verification"], settings)
        if sum(a*b for a,b in zip(*values)) < .99:
            raise ValueError("Repeated input embeddings are inconsistent")
        return {"dimensions": len(values[0]), "repeated_input_verified": True, "semantic_quality_benchmark": False}
    check("ocr_prerequisites", settings.ocr_mode == "auto", ocr)
    check("identity_discovery", settings.auth_mode == "oidc", identity)
    check("model_grounding_probe", settings.model_mode != "extractive", model)
    check("embedding_endpoint", settings.retrieval_mode == "hybrid", embedding)
    return {"schema": "nawa-service-validation-v1", "version": __version__, "created_at": datetime.now(timezone.utc).isoformat(), "scope": "Configured endpoint connectivity and narrow synthetic probes; no user-data accuracy or production certification", "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/service-validation.json")
    args = parser.parse_args()
    result = validate(Settings())
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("; ".join(item["name"] + ": " + item["status"] for item in result["checks"]))
    print("Evidence report:", target)
    raise SystemExit(1 if any(item["status"] == "failed" for item in result["checks"]) else 0)
