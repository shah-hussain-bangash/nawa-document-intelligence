import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    auth_mode: str = field(default_factory=lambda: os.getenv("AUTH_MODE", "demo"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///.data/nawa.db"))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", ".data")))
    seed_demo: bool = field(default_factory=lambda: os.getenv("SEED_DEMO", "true").lower() == "true")
    web_origin: str = field(default_factory=lambda: os.getenv("WEB_ORIGIN", "http://localhost:5173"))
    model_mode: str = field(default_factory=lambda: os.getenv("MODEL_MODE", "extractive"))
    model_url: str = field(default_factory=lambda: os.getenv("MODEL_BASE_URL", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", ""))
    model_key: str = field(default_factory=lambda: os.getenv("MODEL_API_KEY", ""), repr=False)
    model_hosts: str = field(default_factory=lambda: os.getenv("MODEL_ALLOWED_HOSTS", ""))
    model_classes: str = field(default_factory=lambda: os.getenv("MODEL_ALLOWED_CLASSIFICATIONS", "synthetic"))
    oidc_issuer: str = field(default_factory=lambda: os.getenv("OIDC_ISSUER", ""))
    oidc_client: str = field(default_factory=lambda: os.getenv("OIDC_CLIENT_ID", ""))
    oidc_secret: str = field(default_factory=lambda: os.getenv("OIDC_CLIENT_SECRET", ""), repr=False)
    oidc_redirect: str = field(default_factory=lambda: os.getenv("OIDC_REDIRECT_URI", ""))
    ocr_mode: str = field(default_factory=lambda: os.getenv("OCR_MODE", "auto"))
    ocr_languages: str = field(default_factory=lambda: os.getenv("OCR_LANGUAGES", "eng+ara"))
    ocr_max_pages: int = field(default_factory=lambda: int(os.getenv("OCR_MAX_PAGES", "6")))
    retrieval_mode: str = field(default_factory=lambda: os.getenv("RETRIEVAL_MODE", "lexical"))
    embedding_url: str = field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL", "http://127.0.0.1:11434/v1"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", ""))
    embedding_classes: str = field(default_factory=lambda: os.getenv("EMBEDDING_ALLOWED_CLASSIFICATIONS", "synthetic"))
    retrieval_max_chunks: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_MAX_CHUNKS", "240")))
    retrieval_min_cosine: float = field(default_factory=lambda: float(os.getenv("RETRIEVAL_MIN_COSINE", "0.45")))

    def validate(self):
        if self.app_env not in {"local", "test", "production"}:
            raise RuntimeError("APP_ENV must be local, test or production")
        if self.auth_mode not in {"demo", "oidc"}:
            raise RuntimeError("Unknown AUTH_MODE")
        if self.app_env == "production":
            if self.auth_mode != "oidc" or self.seed_demo or not self.web_origin.startswith("https://"):
                raise RuntimeError("Production requires OIDC, HTTPS WEB_ORIGIN and SEED_DEMO=false")
        if self.auth_mode == "oidc" and not all([self.oidc_issuer.startswith("https://"), self.oidc_client, self.oidc_redirect]):
            raise RuntimeError("OIDC requires a trusted HTTPS issuer, client ID and redirect URI")
        if self.model_mode not in {"extractive", "hosted", "ollama"}:
            raise RuntimeError("MODEL_MODE must be extractive, hosted or ollama")
        if self.model_mode == 'ollama':
            from urllib.parse import urlparse
            if not self.model_url:
                self.model_url='http://127.0.0.1:11434/v1'
            parsed=urlparse(self.model_url)
            if self.app_env=='production' or parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path.rstrip('/')!='/v1' or not self.model_name:
                raise RuntimeError('Local Ollama requires local/test mode, a loopback HTTP /v1 endpoint and MODEL_NAME. Production keeps its approved HTTPS route.')
        import re
        if self.ocr_mode not in {"auto", "off"} or not re.fullmatch(r"[A-Za-z0-9_]+(?:\+[A-Za-z0-9_]+)*", self.ocr_languages) or not 1 <= self.ocr_max_pages <= 6:
            raise RuntimeError("OCR requires auto/off, explicit language codes and OCR_MAX_PAGES between 1 and 6")
        if self.retrieval_mode not in {"lexical", "hybrid"} or not 4 <= self.retrieval_max_chunks <= 1000 or not 0 < self.retrieval_min_cosine < 1:
            raise RuntimeError("Invalid bounded retrieval settings")
        if self.retrieval_mode == "hybrid":
            from uae_ai.rag.embeddings import validate_route
            validate_route(self)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "uploads").mkdir(exist_ok=True)

