"""Disposable-DB retrieval fixture, not a production authorization service."""
import hashlib
from uuid import UUID
from .authorization import Principal, authorized
from .identity_repository import membership_by_key
from .retrieval import Passage
from .review import inspect


class SyntheticPostgresPassages:
    """Load approved, latest-version retained TXT sources for synthetic tests.

    This class does not implement a document ACL, exports or an authenticated
    API. Its one-way withdrawal is a synthetic database experiment only.
    """
    def __init__(self, connect, store):
        self.connect = connect
        self.store = store

    def principal(self, subject, tenant):
        with self.connect() as conn:
            return membership_by_key(conn, identity_key=subject, tenant=tenant)

    def passages(self, principal):
        if not authorized(principal, 'view', tenant=principal.tenant):
            raise ValueError('Evidence unavailable')
        with self.connect() as conn:
            current = membership_by_key(conn, identity_key=principal.subject, tenant=principal.tenant, lock=True)
            if current != principal:
                raise ValueError('Evidence unavailable')
            rows = conn.execute('''SELECT d.id,d.filename,d.sha256,v.version,j.result,r.revision,r.ledger
                FROM nawa_intake_versions v
                JOIN nawa_intake_documents d ON d.tenant_id=v.tenant_id AND d.id=v.document_id
                JOIN nawa_intake_jobs j ON j.tenant_id=d.tenant_id AND j.document_id=d.id
                JOIN nawa_intake_promotions p ON p.tenant_id=d.tenant_id AND p.document_id=d.id
                JOIN nawa_reviews r ON r.quotation_id=p.quotation_id
                WHERE v.tenant_id=%s AND j.state='completed'
                  AND NOT EXISTS (SELECT 1 FROM nawa_synthetic_withdrawals w
                    WHERE w.tenant_id=d.tenant_id AND w.document_id=d.id)
                  AND NOT EXISTS (SELECT 1 FROM nawa_intake_versions n
                    WHERE n.tenant_id=v.tenant_id AND n.family_id=v.family_id AND n.version>v.version)
                ORDER BY d.id LIMIT 21''', (principal.tenant,)).fetchall()
            if len(rows) > 20:
                raise ValueError('Evidence unavailable')
            result = []
            for document, filename, digest, version, extracted, revision, ledger in rows:
                review = inspect(ledger)
                if (review['revision'] != revision or review['document'] != filename
                        or not isinstance(extracted, dict) or review['source_evidence'] != extracted.get('evidence')):
                    raise ValueError('Evidence unavailable')
                if review['status'] != 'approved' or not filename.lower().endswith('.txt'):
                    continue
                content = self.store.read_verified(document.hex, digest.strip())
                if len(content) > 65536:
                    raise ValueError('Evidence unavailable')
                text = content.decode('utf-8')
                result.append(Passage.from_dict({'passage_id':document.hex + ':v' + str(version),
                    'document_id':document.hex, 'version':str(version), 'tenant_id':principal.tenant,
                    'page':1, 'text':text, 'allowed_principals':[principal.subject],
                    'source':filename, 'method':'synthetic'}))
            return result

    def withdraw(self, principal, document_id, reason):
        """Record a one-way synthetic withdrawal by a current reviewer."""
        if (not isinstance(principal, Principal) or principal.role != 'reviewer'
                or not authorized(principal, 'view', tenant=principal.tenant)
                or not isinstance(document_id, str) or not isinstance(reason, str)
                or not reason.strip() or len(reason.strip()) > 500):
            raise ValueError('Document unavailable')
        try:
            document = UUID(document_id)
        except ValueError:
            raise ValueError('Document unavailable') from None
        with self.connect() as conn:
            current = membership_by_key(conn, identity_key=principal.subject, tenant=principal.tenant, lock=True)
            if current != principal:
                raise ValueError('Document unavailable')
            row = conn.execute('''SELECT 1 FROM nawa_intake_documents
                WHERE tenant_id=%s AND id=%s FOR UPDATE''', (principal.tenant, document)).fetchone()
            if row is None:
                raise ValueError('Document unavailable')
            actor = hashlib.sha256(principal.subject.encode('utf-8')).hexdigest()
            inserted = conn.execute('''INSERT INTO nawa_synthetic_withdrawals
                (tenant_id,document_id,actor_hash,reason) VALUES (%s,%s,%s,%s)
                ON CONFLICT DO NOTHING RETURNING document_id''',
                (principal.tenant, document, actor, reason.strip())).fetchone()
            return inserted is not None
