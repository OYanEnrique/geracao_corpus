"""Script de entrada para etapa 1 & 2: Preparação e Segmentação."""
import sys
from pathlib import Path

# Garantir que a raiz do projeto esteja no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preparation.pipeline_prepare import run_preparation

if __name__ == "__main__":
    run_preparation()
