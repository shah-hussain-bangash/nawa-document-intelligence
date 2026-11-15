"""Phase 5: deterministic, extractive, citation-linked answers over Phase 4 BM25.

No LLM, no claim of understanding. Only verbatim source sentences are returned.
Trusted caller must supply verified tenant/principal; CLI is a local simulation.
"""
import re
from .retrieval import BM25Index, tokenize

STOP = set(tokenize('''what which who when where why how is are was were the a an of for in on at to from do does did
please tell me show give find document documents quotation quote supplier supplies price total value amount
كم ما هي هو في من عن على إلى لدى لي اذكر اعرض ابحث الوثيقة المستند مستند عرض عروض سعر السعر'''))


def _sentences(text: str) -> list[str]:
    # Retain currency decimals / Arabic fractional numbers rather than cutting within them.
    return [part.strip() for part in re.split(r'(?<=[.!?؟])\s+', text.strip()) if part.strip()]


def ask(index: BM25Index, question: str, *, top_k: int = 5, min_coverage: float = 0.60) -> dict:
    """Return a verbatim sentence and citation, or abstain for insufficient lexical support.

    min_coverage is a transparent lexical gate, not a probability/confidence score.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError('Nonempty question required')
    if not isinstance(min_coverage, (float, int)) or isinstance(min_coverage, bool) or not 0 < min_coverage <= 1:
        raise ValueError('min_coverage must be greater than 0 and at most 1')
    if not isinstance(index, BM25Index):
        raise TypeError('Expected a permission-filtered BM25Index')
    terms = set(tokenize(question)) - STOP
    result = {'question': question, 'tenant_id': index.tenant_id,
              'principal_id': index.principal_id, 'status': 'insufficient_evidence',
              'answer': None, 'citations': [], 'lexical_coverage': 0.0,
              'note': 'Extractive evidence only; lexical coverage is not model confidence'}
    if not terms:
        return result
    matches = index.search(question, k=top_k)
    best = None
    for hit in matches:
        for sentence in [*_sentences(hit['text']), hit['text']]:
            overlap = terms.intersection(tokenize(sentence))
            coverage = len(overlap) / len(terms)
            # Deterministic ordering: support first, BM25 rank second, sentence order third.
            candidate = (coverage, len(overlap))
            if best is None or candidate > best[0]:
                best = (candidate, hit, sentence)
    if best is None:
        return result
    (coverage, matched), hit, sentence = best
    result['lexical_coverage'] = round(coverage, 4)
    # One matching token for a multi-term question is not enough evidence.
    if coverage < min_coverage or (len(terms) > 1 and matched < 2):
        return result
    result.update({'status': 'answered', 'answer': sentence,
                   'citations': [{'passage_id': hit['passage_id'],
                                  'document_id': hit['document_id'],
                                  'version': hit['version'], 'source': hit['source'],
                                  'page': hit['page'], 'method': hit['method'],
                                  'quote': sentence}]})
    return result
