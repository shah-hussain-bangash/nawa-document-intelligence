import json
from pathlib import Path
from uae_ai.main import app
path = Path("docs/implementation/openapi.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
print(path)
