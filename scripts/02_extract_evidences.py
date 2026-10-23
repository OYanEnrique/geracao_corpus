"""Script de entrada para etapa 3: Extração de Evidências."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.extraction.pipeline_extract import run_evidence_extraction

if __name__ == "__main__":
    run_evidence_extraction()
