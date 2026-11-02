"""Script mestre para execução de ponta a ponta do pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_full_pipeline

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Executar pipeline completo de QA para RAG histórico")
    parser.add_argument("--raw_dir", type=str, default="data/raw/piloto_2", help="Diretório de documentos brutos")
    parser.add_argument("--target", type=int, default=10, help="Perguntas por categoria")
    parser.add_argument("--version", type=str, default="v0.4_piloto2_80", help="Tag de versão do benchmark")
    args = parser.parse_args()

    run_full_pipeline(raw_dir=args.raw_dir, target_per_category=args.target, version_tag=args.version)
