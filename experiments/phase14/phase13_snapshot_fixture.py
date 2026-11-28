"""Map fixture-shaped Phase 13 PDF evidence to synthetic search candidates.

This is not a PostgreSQL adapter, identity check, source-integrity check, or
deletion policy. All security-related inputs are test-supplied assertions.
"""
from pathlib import PurePosixPath
import re

from retrieval import Passage

IDENTIFIER = re.compile(r'^[0-9a-f]{32}$')
FIELD = re.compile(r'^[a-z][a-z0-9_]{0,63}$')


def fixture_snapshot(rows, *, tenant, principal, membership_active):
    if (membership_active is not True or not isinstance(tenant, str) or not tenant
            or not isinstance(principal, str) or not principal):
        raise PermissionError('Fixture membership unavailable')
    if not isinstance(rows, list):
        raise ValueError('Invalid fixture rows')
    selected = [row for row in rows if row.get('tenant_id') == tenant]
    seen_documents, seen_versions, families = set(), set(), {}
    for row in selected:
        document, family, version = row.get('document_id'), row.get('family_id'), row.get('version')
        if (not isinstance(document, str) or not IDENTIFIER.fullmatch(document)
                or not isinstance(family, str) or not IDENTIFIER.fullmatch(family)
                or not isinstance(version, int) or isinstance(version, bool) or version < 1):
            raise ValueError('Invalid fixture document metadata')
        if document in seen_documents or (family, version) in seen_versions:
            raise ValueError('Ambiguous fixture version')
        seen_documents.add(document)
        seen_versions.add((family, version))
        if family not in families or version > families[family]['version']:
            families[family] = row
    passages, provenance = [], {}
    for family, row in families.items():
        # Never use an older completed version when a newer one is pending.
        if row.get('job_state') != 'completed':
            continue
        filename, digest, result = row.get('filename'), row.get('sha256'), row.get('result')
        if (row.get('source_verified') is not True or not isinstance(digest, str)
                or not re.fullmatch(r'[0-9a-f]{64}', digest)
                or not isinstance(filename, str) or not filename.lower().endswith('.pdf')
                or PurePosixPath(filename).name != filename or '\\' in filename
                or not isinstance(result, dict) or not isinstance(result.get('evidence'), dict)):
            raise ValueError('Unverified or unsupported fixture evidence')
        for field, citation in result['evidence'].items():
            if (not isinstance(field, str) or not FIELD.fullmatch(field) or not isinstance(citation, dict)
                    or citation.get('method') != 'text_layer'
                    or not isinstance(citation.get('source_text'), str) or not citation['source_text'].strip()
                    or not isinstance(citation.get('page'), int) or isinstance(citation['page'], bool)
                    or citation['page'] < 1
                    or not isinstance(citation.get('page_line'), int) or isinstance(citation['page_line'], bool)
                    or citation['page_line'] < 1):
                raise ValueError('Invalid PDF fixture citation')
            passage_id = row['document_id'] + ':' + field
            raw = citation.get('raw_extracted_text')
            if raw is not None and not isinstance(raw, str):
                raise ValueError('Invalid raw PDF fixture text')
            passages.append(Passage(passage_id, family, str(row['version']), tenant,
                                    citation['page'], citation['source_text'], (principal,),
                                    filename, 'text_layer'))
            provenance[passage_id] = {'source_sha256':digest, 'page_line':citation['page_line'],
                                      'document_id':row['document_id'],
                                      'text_representation':'normalized' if raw is not None
                                      and raw != citation['source_text'] else 'as_extracted'}
    return {'passages':passages, 'lifecycle':{p.passage_id:'current' for p in passages},
            'provenance':provenance}

