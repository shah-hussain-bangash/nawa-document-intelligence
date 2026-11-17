"""Subprocess entry point for the synthetic intake worker."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

from .intake_limits import apply_parser_limits


def main():
    apply_parser_limits()
    from .core import extract
    from .intake_worker import _extract_pdf
    if len(sys.argv) != 2:
        raise ValueError('Expected one input file')
    path = Path(sys.argv[1])
    if path.suffix == '.pdf':
        with TemporaryDirectory(prefix='nawa-parser-') as temp:
            result = _extract_pdf(path.read_bytes(), temp)
    else:
        result = extract(path)
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8'))


if __name__ == '__main__':
    main()

