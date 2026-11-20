"""Synthetic intake TXT correction evidence checks; not a production source service."""
from pathlib import PurePosixPath


def load_intake_text(conn, principal, quotation_id, quotation, store):
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
    if (not isinstance(filename, str) or PurePosixPath(filename).suffix.lower() != '.txt'
            or quotation.get('document') != filename):
        raise ValueError('Synthetic TXT correction source required')
    content = store.read_verified(document_id.hex, digest.strip())
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
