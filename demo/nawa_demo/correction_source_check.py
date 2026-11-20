"""Synthetic intake correction evidence checks; not a production source service."""
import hashlib
import json
from pathlib import PurePosixPath
import subprocess
import sys
import tempfile

PDF_FIXTURE_SHA256 = 'efe191b915a9ba0f205017f9c7911d72422ddb047c9a7ef48c3e728a47499b68'
MAX_LINE_JSON = 2 * 1024 * 1024


def fixture_pdf_lines(content):
    """Re-extract one pinned synthetic fixture in a limited subprocess."""
    if not isinstance(content, bytes) or hashlib.sha256(content).hexdigest() != PDF_FIXTURE_SHA256:
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
        if not isinstance(lines, list) or not lines or not all(isinstance(line, str) for line in lines):
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
            or not excerpt.strip() or excerpt != lines[line - 1]):
        raise ValueError('Synthetic correction evidence does not match source')
