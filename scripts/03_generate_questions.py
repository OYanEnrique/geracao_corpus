"""Script de entrada para etapa 4: Geração Equilibrada de Perguntas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generation.question_generator import run_question_generation

if __name__ == "__main__":
    run_question_generation(target_per_category=4)
