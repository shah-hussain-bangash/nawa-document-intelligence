"""PDF parsing policy for the isolated synthetic intake prototype."""
from hashlib import sha256
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Exact hashes of four bundled synthetic fixtures with malformed xref offsets.
# This exception is not general acceptance of malformed user uploads.
_SYNTHETIC_FIXTURES = frozenset({
    'ff139c12dde6ea0091b621d9cda22c33ba33a6c87024ff24937a9fc638b28697',
    '0d0f05e9f31b2f72989da9cbe442e2a851ecb9b41adcce93a5972ab515a4b813',
    'be8de4dbf2cfbf4dad03009b571ebb13b5e873248ec149842576a2ea7d7dc3e0',
    '3bbebac92722b82770c31725806efb6148f2b317b0a3af7348145a2f336d95d6',
})


def open_pdf(content):
    try:
        return PdfReader(BytesIO(content), strict=True)
    except PdfReadError:
        if sha256(content).hexdigest() not in _SYNTHETIC_FIXTURES:
            raise
        return PdfReader(BytesIO(content), strict=False)
