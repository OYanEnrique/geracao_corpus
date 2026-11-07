"""Orquestrador completo de ponta a ponta do pipeline com comitês de geração e auditoria."""
from pathlib import Path
from typing import Dict, Any

from src.preparation.pipeline_prepare import run_preparation
from src.extraction.pipeline_extract import run_evidence_extraction
from src.generation.committee_generator import run_committee_generation_loop
from src.evaluation.human_review import run_human_review_export
from src.evaluation.benchmark_builder import run_benchmark_builder
from src.evaluation.report_generator import build_and_save_report


def run_full_pipeline(
    raw_dir: str = "data/raw/piloto_2",
    target_per_category: int = 10,
    version_tag: str = "v0.4_piloto2_80",
    force_reextract: bool = True
) -> Dict[str, Any]:
    print("================================================================================")
    print(" INICIANDO PIPELINE COM COMITÊS DE MODELOS (VOTAÇÃO E REJEIÇÃO DE TAUTOLOGIA)")
    print(f" Corpus de Origem: {raw_dir}")
    print(f" Meta: {target_per_category} por categoria | Total: {target_per_category * 8} itens válidos")
    print("================================================================================")

    # 1. Preparação e chunking contextual
    prep_res = run_preparation(raw_dir=raw_dir)

    # 2. Extração atômica de evidências
    extract_res = run_evidence_extraction(sample_chunks_per_doc=1)

    # 3. Geração e Auditoria Contínua com Comitês (3 maiores + 3 menores) e Votação
    committee_res = run_committee_generation_loop(target_per_category=target_per_category)

    # 4. Exportação para protocolo de revisão humana
    review_res = run_human_review_export()

    # 5. Particionamento e congelamento de versão
    bench_res = run_benchmark_builder(version_tag=version_tag)

    # 6. Geração do relatório executivo acumulado sequencialmente em /relatorios
    # Título e contexto derivados dinamicamente do diretório de dados ou metadados
    raw_name = Path(raw_dir).name
    title = f"Acervo Documental ({raw_name})"
    if "piloto_1" in raw_name:
        title = "Discursos Presidenciais do Brasil (1985-2023)"
    elif "piloto_2" in raw_name:
        title = "Discursos Presidenciais dos EUA (1789-2013)"

    report_file = build_and_save_report(
        corpus_title=title,
        corpus_tag=version_tag,
        total_docs=prep_res["documents_count"],
        total_chunks=prep_res["chunks_count"]
    )

    print("================================================================================")
    print(" PIPELINE DE COMITÊS EXECUTADO COM SUCESSO DE PONTA A PONTA!")
    print(f" Total Gold: {bench_res['gold_items_count']} itens aprovados por votação.")
    print(f" Relatório Sequencial salvo em: {report_file}")
    print("================================================================================")

    return {
        "preparation": prep_res,
        "extraction": extract_res,
        "committee": committee_res,
        "human_review": review_res,
        "benchmark": bench_res,
        "report_file": str(report_file)
    }


if __name__ == "__main__":
    run_full_pipeline()
