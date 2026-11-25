"""Backward-compatible wrapper. Prefer: python nawa.py run."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.devtools import main

if __name__ == "__main__":
    raise SystemExit(main(["run", *sys.argv[1:]]))
