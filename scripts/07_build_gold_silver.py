"""Script de entrada para etapa 8: Particionamento e Congelamento Gold/Silver."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.benchmark_builder import run_benchmark_builder

if __name__ == "__main__":
    run_benchmark_builder()
