"""Experimental OCR-to-review handoff contract; not wired to NAWA intake."""
import hashlib
import re

_SHA256 = re.compile(r'[0-9a-f]{64}\Z')

def make_review_handoff(result, *, source_pdf_sha256, source_page):
    """Describe a candidate without producing a promotable quotation.

    Source PDF identity and page are supplied by the caller and have not been
    independently bound to the rendered image by this experimental contract.
    """
    if not isinstance(result, dict) or result.get('status') != 'human_review_required':
        raise ValueError('OCR result is not eligible for handoff')
    if not isinstance(source_page, int) or isinstance(source_page, bool) or not 1 <= source_page <= 50:
        raise ValueError('Invalid source page')
    def digest(value):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError('Invalid SHA-256')
        return value
    pdf_sha = digest(source_pdf_sha256)
    image_sha = digest(result.get('source_sha256'))
    engine_sha = digest(result.get('engine_sha256'))
    models = result.get('model_sha256')
    if not isinstance(models, dict) or not models or len(models) > 2:
        raise ValueError('Invalid language models')
    if not set(models).issubset({'eng.traineddata', 'ara.traineddata'}):
        raise ValueError('Unsupported language model')
    model_hashes = {name:digest(value) for name, value in sorted(models.items())}
    text = result.get('extracted_text_untrusted')
    if not isinstance(text, str) or len(text.encode('utf-8')) > 256 * 1024:
        raise ValueError('Invalid OCR text')
    return {'state':'requires_human_review', 'promotable':False,
            'evidence':{'source_pdf_sha256_unverified':pdf_sha, 'page_unverified':source_page,
                        'rendered_image_sha256':image_sha, 'engine_sha256':engine_sha,
                        'model_sha256':model_hashes,
                        'ocr_text_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
                        'precision':'page_metadata_unverified'},
            'scope':'Experimental synthetic handoff; no quotation or approval is created.'}
