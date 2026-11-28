"""Verify the file bytes for the recorded synthetic case-study replay."""
import hashlib
from pathlib import Path, PurePosixPath


def verify_recorded_inputs(root, record):
    if (not isinstance(record, dict)
            or record.get('source_commit') != '823565f7c44c15b07719b91670fe8bbfb8d96521'
            or not isinstance(record.get('source_file_sha256'), dict)
            or not record['source_file_sha256']):
        raise ValueError('Historical case-study record is invalid')
    root = Path(root).resolve()
    for name, expected in record['source_file_sha256'].items():
        if (not isinstance(name, str) or not name.startswith(('demo/nawa_demo/', 'demo/samples/'))
                or '..' in PurePosixPath(name).parts or not isinstance(expected, str)
                or len(expected) != 64):
            raise ValueError('Historical case-study record is invalid')
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Historical case-study record is invalid')
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            raise ValueError('Historical case-study inputs differ from the recorded baseline') from None
        if actual != expected:
            raise ValueError('Historical case-study inputs differ from the recorded baseline')
