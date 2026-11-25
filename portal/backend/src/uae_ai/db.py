from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, Integer, JSON, Numeric, String, Text, UniqueConstraint, ForeignKeyConstraint, Index, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String(50), primary_key=True)
    name = Column(String(120), nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False)
    role = Column(String(20), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    oidc_subject = Column(String(500), nullable=True, unique=True)
    preferences = Column(JSON, default=dict, nullable=False)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    csrf = Column(String(80), nullable=False)
    expires = Column(Integer, nullable=False)


class OAuthState(Base):
    __tablename__ = "oauth_states"
    id = Column(String(64), primary_key=True)
    verifier = Column(String(120), nullable=False)
    nonce = Column(String(120), nullable=False)
    expires = Column(Integer, nullable=False)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index('uq_documents_id_tenant', 'id', 'tenant_id', unique=True),)
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    created_by = Column(String(50), nullable=False)
    title = Column(String(240), nullable=False)
    filename = Column(String(240), nullable=False)
    category = Column(String(40), default="Policy", nullable=False)
    classification = Column(String(30), default="synthetic", nullable=False)
    allowed_roles = Column(JSON, default=list, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    status = Column(String(30), default="ready", nullable=False)
    processing_token = Column(String(50), default="", server_default="", nullable=False)
    processing_until = Column(Integer, default=0, server_default="0", nullable=False)
    processing_attempts = Column(Integer, default=0, server_default="0", nullable=False)
    version = Column(Integer, default=1, nullable=False)
    content_hash = Column(String(64), nullable=False)
    pages = Column(JSON, default=list, nullable=False)
    size = Column(Integer, default=0, nullable=False)
    source = Column(String(160), default="User upload", nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class DocumentVersion(Base):
    __tablename__ = 'document_versions'
    __table_args__ = (
        UniqueConstraint('document_id', 'version', name='uq_document_version'),
        UniqueConstraint('id', 'tenant_id', name='uq_version_id_tenant'),
        ForeignKeyConstraint(['document_id','tenant_id'], ['documents.id','documents.tenant_id']),
    )
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(String(50), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    filename = Column(String(240), nullable=False)
    content_hash = Column(String(64), nullable=False)
    storage_key = Column(String(160), nullable=False)
    pages = Column(JSON, default=list, nullable=False)
    status = Column(String(30), nullable=False)
    size = Column(Integer, nullable=False)
    created_by = Column(String(50), nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Extraction(Base):
    __tablename__ = 'extractions'
    __table_args__ = (
        UniqueConstraint('id','tenant_id',name='uq_extraction_id_tenant'),
        ForeignKeyConstraint(['version_id','tenant_id'], ['document_versions.id','document_versions.tenant_id']),
    )
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    version_id = Column(String(50), nullable=False, index=True)
    actor_id = Column(String(50), nullable=False)
    extractor_version = Column(String(80), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class ExtractionReview(Base):
    __tablename__ = 'extraction_reviews'
    __table_args__ = (ForeignKeyConstraint(['extraction_id','tenant_id'], ['extractions.id','extractions.tenant_id']),)
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    extraction_id = Column(String(50), nullable=False, index=True)
    actor_id = Column(String(50), nullable=False)
    values = Column(JSON, nullable=False)
    changes = Column(JSON, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Case(Base):
    __tablename__ = "cases"
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    reference = Column(String(40), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="", nullable=False)
    department = Column(String(100), nullable=False)
    created_by = Column(String(50), nullable=False)
    budget = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="AED", nullable=False)
    due_date = Column(String(10), nullable=False)
    priority = Column(String(15), default="Normal", nullable=False)
    status = Column(String(30), default="draft", nullable=False)
    revision = Column(Integer, default=1, nullable=False)
    evidence_versions = Column(JSON, default=dict, server_default="{}", nullable=False)
    document_ids = Column(JSON, default=list, nullable=False)
    quotes = Column(JSON, default=list, nullable=False)
    comparison = Column(JSON, default=dict, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Run(Base):
    __tablename__ = "workflow_runs"
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    case_id = Column(String(50), nullable=False, index=True)
    actor_id = Column(String(50), nullable=False)
    request_key = Column(String(160), nullable=False, unique=True)
    fingerprint = Column(String(64), nullable=False)
    revision = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
    execution_token = Column(String(50), default="", server_default="", nullable=False)
    execution_until = Column(Integer, default=0, server_default="0", nullable=False)
    snapshot = Column(String(64), default="", nullable=False)
    steps = Column(JSON, default=list, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (Index('uq_approval_run', 'run_id', unique=True),)
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    case_id = Column(String(50), nullable=False, index=True)
    run_id = Column(String(50), nullable=False)
    revision = Column(Integer, nullable=False)
    snapshot = Column(String(64), nullable=False)
    requested_by = Column(String(50), nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    decision_by = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(String(40), default=now, nullable=False)
    decided_at = Column(String(40), nullable=True)


class Audit(Base):
    __tablename__ = "audit_events"
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    actor = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String(50), primary_key=True, default=uid)
    tenant_id = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(40), nullable=False)
    priority = Column(String(15), nullable=False)
    status = Column(String(20), default="Open", nullable=False)
    created_by = Column(String(120), nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


def make_database(url):
    options = {"connect_args": {"check_same_thread": False, "timeout": 20}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    engine = create_engine(url, **options)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def sqlite_config(connection, _):
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
    return engine, sessionmaker(bind=engine, expire_on_commit=False)

