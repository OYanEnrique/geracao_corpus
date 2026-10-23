"""Script de entrada para etapa 6: Validação Automática Independente."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.validation.auto_validator import run_auto_validation

if __name__ == "__main__":
    run_auto_validation()
