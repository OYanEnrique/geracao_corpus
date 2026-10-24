"""Orquestrador completo de ponta a ponta do pipeline com comitês de geração e auditoria."""
from typing import Dict, Any

from src.preparation.pipeline_prepare import run_preparation
from src.extraction.pipeline_extract import run_evidence_extraction
from src.generation.committee_generator import run_committee_generation_loop
from src.evaluation.human_review import run_human_review_export
from src.evaluation.benchmark_builder import run_benchmark_builder


def run_full_pipeline(target_per_category: int = 10, version_tag: str = "v0.3_committee_80") -> Dict[str, Any]:
    print("================================================================================")
    print(" INICIANDO PIPELINE COM COMITÊS DE MODELOS (VOTAÇÃO E REJEIÇÃO DE TAUTOLOGIA)")
    print(f" Meta: {target_per_category} por categoria | Total: {target_per_category * 8} itens válidos")
    print("================================================================================")

    # 1. Preparação e chunking contextual (se necessário)
    from pathlib import Path
    if not Path("corpus/chunks.jsonl").exists() or Path("corpus/chunks.jsonl").stat().st_size == 0:
        prep_res = run_preparation()
    else:
        prep_res = {"status": "already_prepared"}

    # 2. Extração atômica de evidências (se necessário)
    if not Path("corpus/evidences.jsonl").exists() or Path("corpus/evidences.jsonl").stat().st_size == 0:
        extract_res = run_evidence_extraction(sample_chunks_per_doc=1)
    else:
        extract_res = {"status": "already_extracted"}

    # 3. Geração e Auditoria Contínua com Comitês (3 maiores + 3 menores) e Votação
    committee_res = run_committee_generation_loop(target_per_category=target_per_category)

    # 4. Exportação para protocolo de revisão humana
    review_res = run_human_review_export()

    # 5. Particionamento e congelamento de versão
    bench_res = run_benchmark_builder(version_tag=version_tag)

    print("================================================================================")
    print(" PIPELINE DE COMITÊS EXECUTADO COM SUCESSO DE PONTA A PONTA!")
    print(f" Total Gold: {bench_res['gold_items_count']} itens aprovados por votação.")
    print("================================================================================")

    return {
        "preparation": prep_res,
        "extraction": extract_res,
        "committee": committee_res,
        "human_review": review_res,
        "benchmark": bench_res
    }


if __name__ == "__main__":
    run_full_pipeline()


if __name__ == "__main__":
    run_full_pipeline()
