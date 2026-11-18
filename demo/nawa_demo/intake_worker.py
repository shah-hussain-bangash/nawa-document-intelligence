"""Offline synthetic quotation worker; no OCR or production isolation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
from .core import extract
from .intake_pdf import open_pdf


class IncompleteArabicPDF(ValueError):
    """Synthetic pypdf extraction saw Arabic but could not resolve required fields."""


def _extract_pdf(content, temp):
    reader = open_pdf(content)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 50:
        raise ValueError('Unsupported PDF')
    lines, locations = [], []
    total_chars = 0
    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        total_chars += len(text)
        if total_chars > 1024 * 1024:
            raise ValueError('Extracted text exceeds prototype limit')
        for line_number, line in enumerate(text.splitlines(), 1):
            lines.append(line)
            locations.append((page_number, line_number))
    if not any(line.strip() for line in lines):
        raise ValueError('No selectable text')
    path = Path(temp) / 'source.txt'
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    try:
        result = extract(path)
    except ValueError as exc:
        contains_arabic=any('\u0600' <= char <= '\u06ff' or '\ufb50' <= char <= '\ufdff'
                            or '\ufe70' <= char <= '\ufeff' for line in lines for char in line)
        if str(exc).startswith('Missing required fields: ') and contains_arabic:
            raise IncompleteArabicPDF('Synthetic Arabic field extraction incomplete') from exc
        raise
    result['input_type'] = 'text_layer_pdf'
    result['page_count'] = len(reader.pages)
    result['evidence_precision'] = 'page_and_extracted_line_only'
    for evidence in result['evidence'].values():
        evidence['page'], evidence['page_line'] = locations[evidence['line'] - 1]
        evidence['method'] = 'text_layer'
    return result


def process_one(jobs, store, tenant, *, worker='synthetic-worker', max_attempts=3, timeout=20):
    if timeout <= 0 or timeout >= 60:
        raise ValueError('Timeout must be between 0 and 60 seconds')
    claim = jobs.claim(tenant, worker, max_attempts=max_attempts)
    if claim is None:
        return None
    job_id, token = claim
    try:
        document_id, filename, digest = jobs.claimed_document(tenant, job_id, token)
        content = store.read_verified(document_id, digest)
        with TemporaryDirectory(prefix='nawa-intake-') as temp:
            path = Path(temp) / ('source.pdf' if Path(filename).suffix.lower() == '.pdf' else 'source.txt')
            output = Path(temp) / 'result.json'
            path.write_bytes(content)
            with output.open('wb') as stream:
                subprocess.run([sys.executable, '-m', 'nawa_demo.intake_parser', str(path)],
                               stdout=stream, stderr=subprocess.DEVNULL, check=True, timeout=timeout)
            with output.open('rb') as stream:
                encoded = stream.read(2 * 1024 * 1024 + 1)
            if len(encoded) > 2 * 1024 * 1024:
                raise ValueError('Parser result too large')
            result = json.loads(encoded.decode('utf-8'))
        result['document'] = filename
    except Exception:
        # Do not expose document contents or parser exception details.
        return jobs.finish(tenant, job_id, token, success=False, max_attempts=max_attempts)
    return jobs.finish(tenant, job_id, token, success=True, result=result, max_attempts=max_attempts)

