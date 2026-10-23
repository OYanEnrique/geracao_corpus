"""Script de entrada para etapa 7: Exportação para Revisão Humana."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.human_review import run_human_review_export

if __name__ == "__main__":
    run_human_review_export()
