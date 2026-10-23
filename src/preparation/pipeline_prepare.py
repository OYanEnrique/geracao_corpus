"""Pipeline de preparação e segmentação dos documentos."""
import csv
import json
from pathlib import Path
from typing import Dict, Any, List

from src.preparation.cleaner import TextCleaner
from src.preparation.chunker import ContextualSentenceChunker
from src.validation.schema_validator import SchemaValidator
from src.utils.config import get_pipeline_config


def run_preparation(raw_dir: str = "data/raw/piloto_1", output_dir: str = "corpus") -> Dict[str, Any]:
    print("=== [Pipeline] Preparação e Segmentação Contextual dos Documentos ===")
    raw_path = Path(raw_dir)
    metadata_csv = raw_path / "metadados_discursos.csv"
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)

    config = get_pipeline_config()
    chunk_cfg = config.get("chunking", {})
    target_chars = chunk_cfg.get("target_chars", 1600)
    overlap_chars = chunk_cfg.get("overlap_chars", 300)

    validator = SchemaValidator()
    chunker = ContextualSentenceChunker(target_chars=target_chars, overlap_chars=overlap_chars)

    documents_out = out_path / "documents.jsonl"
    chunks_out = out_path / "chunks.jsonl"

    documents_list: List[Dict[str, Any]] = []
    chunks_list: List[Dict[str, Any]] = []

    with open(metadata_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Ingerindo {len(rows)} documentos de {metadata_csv}...")

    for row in rows:
        doc_id = row["id_doc"]
        filename = row["arquivo_bruto"]
        file_path = raw_path / filename

        if not file_path.exists():
            print(f"[Aviso] Arquivo bruto não encontrado: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as tf:
            raw_text = tf.read()

        clean_text, stats = TextCleaner.clean(raw_text)
        quality = TextCleaner.estimate_quality(clean_text)

        doc_record = {
            "document_id": doc_id,
            "collection": "discursos_presidenciais_pos_redemocratizacao",
            "doc_type": row["tipo_discurso"],
            "title": f"Pronunciamento Presidencial de {row['presidente']} ({row['ano']})",
            "date": row["ano"],
            "author": row["presidente"],
            "page_count": 1,
            "ocr_quality_overall": quality,
            "archival_context": "Discursos de posse e pronunciamentos de chefes de Estado (1985-2023)",
            "file_ref": str(file_path.as_posix()),
            "metadata": {
                "caso_limitrofe": row.get("caso_limitrofe") == "True",
                "observacao": row.get("observacao", ""),
                "char_length_original": stats["original_length"],
                "char_length_cleaned": stats["cleaned_length"]
            }
        }

        is_valid, errors = validator.validate("document", doc_record)
        if not is_valid:
            print(f"[Erro de Schema em {doc_id}]: {errors}")
        else:
            documents_list.append(doc_record)

        doc_chunks = chunker.chunk_document(doc_id=doc_id, text=clean_text, page=1)
        for c in doc_chunks:
            c["ocr_quality"] = quality
        chunks_list.extend(doc_chunks)

    with open(documents_out, "w", encoding="utf-8") as f:
        for doc in documents_list:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    with open(chunks_out, "w", encoding="utf-8") as f:
        for chunk in chunks_list:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    summary = {
        "documents_count": len(documents_list),
        "chunks_count": len(chunks_list),
        "documents_path": str(documents_out),
        "chunks_path": str(chunks_out)
    }
    print(f"[OK] Preparação concluída: {len(documents_list)} documentos e {len(chunks_list)} chunks contextuais.")
    return summary


if __name__ == "__main__":
    run_preparation()
