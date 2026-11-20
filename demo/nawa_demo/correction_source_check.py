"""Synthetic intake correction evidence checks; not a production source service."""
import hashlib
import json
from pathlib import PurePosixPath
import subprocess
import sys
import tempfile

PDF_FIXTURE_SHA256 = frozenset({
    'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68',
    '3bbebac92722b82770c31725806efb6148f2b317b0a3af7348145a2f336d95d6',
    '1b95cabe02ceca5f7e9f71216c3f9b1ef6e8e41a546faea053641ab7a71fad03',
})
MAX_LINE_JSON = 2 * 1024 * 1024


def fixture_pdf_lines(content):
    """Re-extract pinned synthetic fixtures in a limited subprocess."""
    if not isinstance(content, bytes) or hashlib.sha256(content).hexdigest() not in PDF_FIXTURE_SHA256:
        raise ValueError('Unsupported synthetic PDF correction source')
    try:
        with tempfile.TemporaryFile() as output:
            subprocess.run([sys.executable, '-m', 'nawa_demo.synthetic_pdf_source_lines'],
                           input=content, stdout=output, stderr=subprocess.DEVNULL, check=True, timeout=20)
            output.seek(0)
            raw = output.read(MAX_LINE_JSON + 1)
        if len(raw) > MAX_LINE_JSON:
            raise ValueError('Synthetic PDF text exceeds limit')
        lines = json.loads(raw.decode('utf-8'))
        if (not isinstance(lines, list) or not lines or not all(
                isinstance(line, dict) and set(line) == {'text', 'page', 'page_line'}
                and isinstance(line['text'], str) and type(line['page']) is int and 1 <= line['page'] <= 2
                and type(line['page_line']) is int and line['page_line'] >= 1 for line in lines)):
            raise ValueError('Invalid synthetic PDF lines')
        return lines
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        raise ValueError('Synthetic PDF correction source unavailable') from None


def load_intake_text(conn, principal, quotation_id, quotation, store, *, allow_fixture_pdf=False):
    """Read the tenant's promoted source with its stored digest; fail closed."""
    if store is None:
        raise ValueError('Synthetic correction source unavailable')
    row = conn.execute('''SELECT d.id,d.filename,d.sha256 FROM nawa_intake_promotions p
        JOIN nawa_intake_documents d ON d.id=p.document_id AND d.tenant_id=p.tenant_id
        WHERE p.tenant_id=%s AND p.quotation_id=%s FOR SHARE OF p,d''',
        (principal.tenant, quotation_id)).fetchone()
    if row is None:
        raise ValueError('Synthetic correction source unavailable')
    document_id, filename, digest = row
    if not isinstance(filename, str) or quotation.get('document') != filename:
        raise ValueError('Synthetic correction source required')
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix != '.txt' and not (allow_fixture_pdf and suffix == '.pdf'):
        raise ValueError('Supported synthetic correction source required')
    content = store.read_verified(document_id.hex, digest.strip())
    if suffix == '.pdf':
        return filename, fixture_pdf_lines(content)
    try:
        return filename, content.decode('utf-8').splitlines()
    except UnicodeDecodeError:
        raise ValueError('Synthetic correction source must be UTF-8') from None


def verify_line(source, line, excerpt, filename, lines):
    """Require an exact original line; this does not prove the corrected value."""
    if (not isinstance(source, str) or source != filename or type(line) is not int
            or line < 1 or line > len(lines) or not isinstance(excerpt, str)
            or not excerpt.strip()):
        raise ValueError('Synthetic correction evidence does not match source')
    entry = lines[line - 1]
    text = entry['text'] if isinstance(entry, dict) else entry
    if excerpt != text:
        raise ValueError('Synthetic correction evidence does not match source')
    if isinstance(entry, dict):
        return {'kind':'pdf_text_layer', 'global_line':line, 'page':entry['page'], 'page_line':entry['page_line']}
    return {'kind':'txt_line', 'line':line}
