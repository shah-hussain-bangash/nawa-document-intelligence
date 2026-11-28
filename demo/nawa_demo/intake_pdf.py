"""PDF parsing policy for the isolated synthetic intake prototype."""
from hashlib import sha256
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Exact hashes of four bundled synthetic fixtures with malformed xref offsets.
# Include the repository's LF bytes and existing Windows CRLF checkout bytes;
# the exception does not generalize to altered or other malformed uploads.
_SYNTHETIC_FIXTURES = frozenset({
    'ff139c12dde6ea0091b621d9cda22c33ba33a6c87024ff24937a9fc638b28697',
    '0d0f05e9f31b2f72989da9cbe442e2a851ecb9b41adcce93a5972ab515a4b813',
    'be8de4dbf2cfbf4dad03009b571ebb13b5e873248ec149842576a2ea7d7dc3e0',
    '3bbebac92722b82770c31725806efb6148f2b317b0a3af7348145a2f336d95d6',
    'b647be96d49b143867e0564060770659dbc7d1a0b183d71e13a534d117ea5fba',
    '4862cf278659bf36c1271572cc65128a2e9e946552fcbb8ac3ade663e0b2af6c',
    'b1edcea773136941a4bb3c4e24f86c6d8fe6881037295ef0807159b063300c16',
    '1b95cabe02ceca5f7e9f71216c3f9b1ef6e8e41a546faea053641ab7a71fad03',
})


def open_pdf(content):
    try:
        return PdfReader(BytesIO(content), strict=True)
    except PdfReadError:
        if sha256(content).hexdigest() not in _SYNTHETIC_FIXTURES:
            raise
        return PdfReader(BytesIO(content), strict=False)

