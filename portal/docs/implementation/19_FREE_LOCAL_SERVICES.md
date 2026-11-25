# Free local service selection — current at v0.6.0

Default: SQLite, BM25 and extractive answers; no model key or paid cloud account.
Optional: Ollama for local embeddings/generation, Keycloak for real local HTTPS
identity, and PostgreSQL through Compose. These use your own hardware, storage,
electricity and model downloads; no permanently free production hosting is promised.

The complete tested setup, commands and limits are in
[20_V060_OCR_HYBRID_AND_RECOVERY.md](20_V060_OCR_HYBRID_AND_RECOVERY.md).

## Optional generation

```powershell
docker compose -f compose.free-services.yaml up -d
docker compose -f compose.free-services.yaml exec ollama ollama pull qwen2.5:1.5b
```

Review model licence/resource needs. Stop the app and set local `.env`:

```dotenv
MODEL_MODE=ollama
MODEL_BASE_URL=http://127.0.0.1:11434/v1
MODEL_NAME=qwen2.5:1.5b
MODEL_ALLOWED_CLASSIFICATIONS=synthetic
```

No MODEL_API_KEY is needed. Run Python on the host; loopback inside a container
refers to that container. Generation and hybrid embedding are independent options.
The local route is restricted to local/test loopback HTTP /v1, no URL credentials,
query or fragment, and no production mode. Unavailable/invalid output fails without
an alternate provider. Citation indices do not prove factual accuracy.

Use `py -3.12 nawa.py services` for configured endpoint probes. Guide 20 includes
hybrid embedding settings, trusted local TLS/Keycloak provisioning and an opt-in
real authorization-code test with private synthetic fixtures. No TLS checks are
disabled and no passwords/tokens are printed or packaged.

## Actual verification

Keycloak 26.4.7 ran and passed seven real local identity checks. Ollama 0.11.10
started, but the cloud proxy denied registry.ollama.ai model downloads. Neither
real generation nor embedding quality is claimed tested. Use the included checks
on your PC after the models download successfully. Small models are examples,
not guaranteed bilingual accuracy. See guide 18 for remaining acceptance gates.

Stop optional model services with `docker compose -f compose.free-services.yaml stop`.
Do not delete volumes if you want to keep downloaded models. Keep CI/cloud usage
within your own budget; no billed infrastructure is provisioned by this release.
