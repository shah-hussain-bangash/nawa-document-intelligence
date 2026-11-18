"""Synthetic citation resolution for human review, not an authenticated API."""
import hashlib
from lifecycle_fixture import recheck_results


def resolve_for_review(review, *, tenant, principal, load_snapshot):
    """Recheck every citation using a fresh source-verified fixture snapshot.

    Document text is returned solely as untrusted content for human inspection.
    The caller must use authenticated identity and safe output rendering.
    """
    try:
        if not isinstance(review, dict) or review.get('status') != 'requires_human_review':
            raise ValueError('Review unavailable')
        citations = review.get('evidence')
        if not isinstance(citations, list) or not 1 <= len(citations) <= 100:
            raise ValueError('Invalid citations')
        required = {'passage_id','document_id','version','page','source',
                    'source_document_id','source_sha256','page_line','evidence_text_sha256'}
        if any(not isinstance(c, dict) or set(c) != required for c in citations):
            raise ValueError('Invalid citation metadata')
        snapshot = load_snapshot()
        provenance = snapshot['provenance']
        if not isinstance(provenance, dict):
            raise ValueError('Provenance unavailable')
        ids = [c['passage_id'] for c in citations]
        passages = recheck_results(snapshot['passages'], ids, tenant=tenant,
                                   principal=principal, lifecycle=snapshot['lifecycle'])
        resolved = []
        for citation, passage in zip(citations, passages):
            info = provenance[passage.passage_id]
            expected = {'passage_id':passage.passage_id, 'document_id':passage.document_id,
                        'version':passage.version, 'page':passage.page, 'source':passage.source,
                        'source_document_id':info['document_id'], 'source_sha256':info['source_sha256'],
                        'page_line':info['page_line'],
                        'evidence_text_sha256':hashlib.sha256(passage.text.encode('utf-8')).hexdigest()}
            if citation != expected:
                raise ValueError('Citation changed')
            resolved.append({'citation':expected, 'untrusted_source_text':passage.text})
        return {'status':'requires_human_review','evidence':resolved}
    except (ValueError, TypeError, KeyError, OSError, TimeoutError):
        return {'status':'unavailable'}

