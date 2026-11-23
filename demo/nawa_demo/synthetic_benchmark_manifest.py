"""Validate synthetic benchmark metadata; does not validate document labels."""
import re

_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z', re.ASCII)
_LANGUAGES = {'ar', 'en', 'mixed'}
_FORMATS = {'scanned_pdf', 'digital_pdf'}
_SPLITS = {'development', 'holdout'}
_STATUSES = {'draft', 'reviewed'}


def _identifier(value):
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def inspect_manifest(manifest):
    """Validate IDs and declared splits, and summarize proposed pilot counts.

    Labels, permissions and template IDs are self-reported, not independently
    checked. The output is not an accuracy score or an authorization decision.
    """
    if (not isinstance(manifest, dict) or set(manifest) != {'schema_version','documents','queries'}
            or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
            or not isinstance(manifest['documents'], list) or not isinstance(manifest['queries'], list)
            or len(manifest['documents']) > 10000 or len(manifest['queries']) > 100000):
        raise ValueError('Invalid synthetic benchmark manifest')
    documents, templates = {}, {}
    doc_fields = {'id','template_id','language','format','split','label_status','source_type'}
    for item in manifest['documents']:
        if (not isinstance(item, dict) or set(item) != doc_fields
                or not _identifier(item['id']) or not _identifier(item['template_id'])
                or not isinstance(item['language'], str) or item['language'] not in _LANGUAGES
                or not isinstance(item['format'], str) or item['format'] not in _FORMATS
                or not isinstance(item['split'], str) or item['split'] not in _SPLITS
                or not isinstance(item['label_status'], str) or item['label_status'] not in _STATUSES
                or item['source_type'] != 'synthetic' or item['id'] in documents):
            raise ValueError('Invalid synthetic document metadata')
        prior = templates.setdefault(item['template_id'], item['split'])
        if prior != item['split']:
            raise ValueError('A declared template is shared across splits')
        documents[item['id']] = item

    query_fields = {'id','language','split','principal_fixture','answerable','expected_document_ids'}
    query_ids = set()
    for item in manifest['queries']:
        if (not isinstance(item, dict) or set(item) != query_fields
                or not _identifier(item['id']) or not _identifier(item['principal_fixture'])
                or not isinstance(item['language'], str) or item['language'] not in _LANGUAGES
                or not isinstance(item['split'], str) or item['split'] not in _SPLITS
                or type(item['answerable']) is not bool or not isinstance(item['expected_document_ids'], list)
                or not all(_identifier(doc) for doc in item['expected_document_ids'])
                or len(item['expected_document_ids']) != len(set(item['expected_document_ids']))
                or bool(item['expected_document_ids']) != item['answerable'] or item['id'] in query_ids):
            raise ValueError('Invalid synthetic query metadata')
        if any(doc not in documents or documents[doc]['split'] != item['split']
               for doc in item['expected_document_ids']):
            raise ValueError('Expected source is missing or outside the declared split')
        query_ids.add(item['id'])

    counts = {language:{fmt:sum(d['language'] == language and d['format'] == fmt
                               for d in documents.values()) for fmt in sorted(_FORMATS)}
              for language in sorted(_LANGUAGES)}
    splits = {split:sum(d['split'] == split for d in documents.values()) for split in sorted(_SPLITS)}
    queries = {language:sum(q['language'] == language and q['split'] == 'holdout'
                            for q in manifest['queries']) for language in sorted(_LANGUAGES)}
    return {'status':'metadata_valid', 'documents_by_language_and_format':counts,
            'documents_by_split':splits, 'holdout_queries_by_language':queries,
            'draft_labels':sum(d['label_status'] != 'reviewed' for d in documents.values()),
            'note':'Declared metadata only; independence, permissions and label correctness are not verified.'}
