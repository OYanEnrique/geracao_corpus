"""Script de entrada para etapa 5: Geração de Respostas de Referência."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generation.answer_generator import run_answer_generation

if __name__ == "__main__":
    run_answer_generation()
