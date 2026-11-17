"""Local synthetic-file prototype; not a tenant-aware or production storage service."""
from hashlib import sha256
from pathlib import Path
import re
import stat
from uuid import uuid4
import os

from .intake_validation import MAX_DOCUMENT_BYTES, check_document

_ID = re.compile(r'^[0-9a-f]{32}$')
_HASH = re.compile(r'^[0-9a-f]{64}$')


class LocalIntakeStore:
    """Save checked bytes under random IDs in a private, application-owned directory.

    Metadata persistence, tenant authorization, backups and retention are not
    implemented. Callers must not use this prototype for real documents.
    """
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, filename, content):
        metadata = check_document(filename, content)
        document_id = uuid4().hex
        path = self.directory / document_id
        created = False
        try:
            with path.open('xb') as stream:
                created = True
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            if created:
                path.unlink(missing_ok=True)
            raise
        return document_id, metadata

    def read_verified(self, document_id, expected_sha256):
        if not isinstance(document_id, str) or not _ID.fullmatch(document_id):
            raise ValueError('Invalid document ID')
        if not isinstance(expected_sha256, str) or not _HASH.fullmatch(expected_sha256):
            raise ValueError('Invalid document digest')
        path = self.directory / document_id
        fd = None
        try:
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode):
                raise ValueError('Document source is not a regular file')
            flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
            fd = os.open(path, flags)
            opened = os.fstat(fd)
            after = path.lstat()
            if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(after.st_mode)
                    or not os.path.samestat(before, opened) or not os.path.samestat(after, opened)):
                raise ValueError('Document source changed during opening')
            with os.fdopen(fd, 'rb') as stream:
                fd = None
                content = stream.read(MAX_DOCUMENT_BYTES + 1)
        except OSError as exc:
            raise ValueError('Document source unavailable') from exc
        finally:
            if fd is not None:
                os.close(fd)
        if len(content) > MAX_DOCUMENT_BYTES or sha256(content).hexdigest() != expected_sha256:
            raise ValueError('Document integrity check failed')
        return content

    def discard(self, document_id):
        """Remove a newly created unregistered file after a failed submission."""
        if not isinstance(document_id, str) or not _ID.fullmatch(document_id):
            raise ValueError('Invalid document ID')
        (self.directory / document_id).unlink(missing_ok=True)

