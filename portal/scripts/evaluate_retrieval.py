"""Small source-relevance smoke check; no external model and no production claim."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uae_ai.core.config import Settings
from uae_ai.core.security import readable_documents
from uae_ai.db import Base, User, make_database
from uae_ai.rag.retrieval import search
from uae_ai.seed import seed

suite = json.loads(Path("evals/retrieval-smoke.json").read_text())
results = []
with TemporaryDirectory() as temp:
    settings = Settings(app_env="test", data_dir=Path(temp), database_url=f"sqlite:///{temp}/eval.db")
    settings.validate()
    engine, factory = make_database(settings.database_url)
    Base.metadata.create_all(engine)
    with factory() as db:
        seed(db, settings)
        documents = readable_documents(db, db.get(User, "operations-analyst"))
        for question in suite["questions"]:
            found = search(question["question"], documents)
            titles = [item["title"] for item in found]
            passed = not titles if question["expected_title"] is None else question["expected_title"] in titles
            results.append({**question, "retrieved_titles": titles, "passed": passed})
    engine.dispose()
report = {"notice": suite["notice"], "retrieval": "local lexical", "passed": sum(r["passed"] for r in results), "total": len(results), "results": results}
destination = Path("artifacts/retrieval-smoke-report.json")
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print(f"{report['passed']}/{report['total']} developer-authored retrieval smoke cases passed. Report: {destination}")
raise SystemExit(0 if all(r["passed"] for r in results) else 1)
