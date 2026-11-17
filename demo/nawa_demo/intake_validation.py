"""Initial synthetic document intake checks; not connected to the dashboard."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath, PureWindowsPath
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
MAX_PDF_PAGES = 50


@dataclass(frozen=True)
class CheckedDocument:
    filename: str
    media_type: str
    size: int
    sha256: str


def check_document(filename: str, content: bytes) -> CheckedDocument:
    """Check a synthetic file and return metadata; not a PDF security scanner."""
    if (not isinstance(filename, str) or not filename or len(filename) > 100
            or filename.startswith('.') or any(ord(c) < 32 or ord(c) == 127 for c in filename)
            or '/' in filename or '\\' in filename or ':' in filename
            or PurePosixPath(filename).name != filename
            or PureWindowsPath(filename).name != filename):
        raise ValueError('Invalid filename')
    if not isinstance(content, bytes) or not 0 < len(content) <= MAX_DOCUMENT_BYTES:
        raise ValueError('Document must contain between 1 byte and 4 MiB')
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix == '.txt':
        if b'\x00' in content:
            raise ValueError('Text contains a null byte')
        try:
            content.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError('Text must be UTF-8') from exc
        if content.startswith(b'%PDF-'):
            raise ValueError('PDF content does not match text extension')
        media_type = 'text/plain'
    elif suffix == '.pdf':
        if not content.startswith(b'%PDF-'):
            raise ValueError('PDF signature is missing')
        try:
            with TemporaryDirectory(prefix='nawa-preflight-') as temp:
                path = Path(temp) / 'source.pdf'
                path.write_bytes(content)
                subprocess.run([sys.executable, '-m', 'nawa_demo.intake_pdf_preflight', str(path)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               check=True, timeout=10)
        except (subprocess.SubprocessError, OSError) as exc:
            raise ValueError('PDF validation failed or exceeded its time limit') from exc
        media_type = 'application/pdf'
    else:
        raise ValueError('Only TXT and PDF files are supported')
    return CheckedDocument(filename, media_type, len(content), sha256(content).hexdigest())
