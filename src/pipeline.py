"""Orquestrador completo de ponta a ponta do pipeline de geração de corpus."""
from typing import Dict, Any

from src.preparation.pipeline_prepare import run_preparation
from src.extraction.pipeline_extract import run_evidence_extraction
from src.generation.question_generator import run_question_generation
from src.generation.answer_generator import run_answer_generation
from src.validation.auto_validator import run_auto_validation
from src.evaluation.human_review import run_human_review_export
from src.evaluation.benchmark_builder import run_benchmark_builder


def run_full_pipeline(target_per_category: int = 4, version_tag: str = "v0.2_balanced") -> Dict[str, Any]:
    print("================================================================================")
    print(" INICIANDO PIPELINE PROFISSIONAL DE GERAÇÃO DE CORPUS HISTÓRICO VERIFICÁVEL")
    print("================================================================================")

    # 1. Preparação e chunking contextual
    prep_res = run_preparation()

    # 2. Extração atômica de evidências
    extract_res = run_evidence_extraction(sample_chunks_per_doc=1)

    # 3. Geração balanceada de perguntas (8 categorias do guia)
    q_res = run_question_generation(target_per_category=target_per_category)

    # 4. Geração de respostas de referência anti-tautológicas
    a_res = run_answer_generation()

    # 5. Validação automática independente com LLM B
    val_res = run_auto_validation()

    # 6. Exportação para protocolo de revisão humana
    review_res = run_human_review_export()

    # 7. Particionamento e congelamento de versão
    bench_res = run_benchmark_builder(version_tag=version_tag)

    print("================================================================================")
    print(" PIPELINE EXECUTADO COM SUCESSO DE PONTA A PONTA!")
    print("================================================================================")

    return {
        "preparation": prep_res,
        "extraction": extract_res,
        "questions": q_res,
        "answers": a_res,
        "validation": val_res,
        "human_review": review_res,
        "benchmark": bench_res
    }


if __name__ == "__main__":
    run_full_pipeline()
