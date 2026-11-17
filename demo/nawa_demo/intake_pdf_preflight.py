"""Timed subprocess for synthetic PDF preflight, not a security sandbox."""
from pathlib import Path
import sys

from .intake_limits import apply_parser_limits


def main():
    apply_parser_limits()
    from .intake_pdf import open_pdf
    if len(sys.argv) != 2:
        raise ValueError('Expected one input file')
    reader = open_pdf(Path(sys.argv[1]).read_bytes())
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 50:
        raise ValueError('Unsupported PDF')


if __name__ == '__main__':
    main()

