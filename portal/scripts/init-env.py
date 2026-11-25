"""Backward-compatible local configuration initialiser."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_config import initialise_env

if __name__ == "__main__":
    print(initialise_env(Path(__file__).resolve().parents[1]))

