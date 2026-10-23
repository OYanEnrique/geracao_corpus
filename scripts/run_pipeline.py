"""Script mestre para execução de ponta a ponta do pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_full_pipeline

if __name__ == "__main__":
    run_full_pipeline(target_per_category=4, version_tag="v0.2_balanced")
