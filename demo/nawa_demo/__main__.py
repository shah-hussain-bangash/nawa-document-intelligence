import argparse
from pathlib import Path
from .core import compare, write_json


def main():
    parser = argparse.ArgumentParser(description="NAWA synthetic Arabic/English quotation comparison demo")
    parser.add_argument("quotations", nargs="+", type=Path, help="UTF-8 quotation files")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()
    try:
        print(write_json(compare(args.quotations), args.output))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
