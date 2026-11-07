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

        # Separar metadados tabulados embutidos se presentes (ex.: piloto_2)
        if "\t" in raw_text[:200]:
            parts = raw_text.split("\t", 2)
            speech_body = parts[2] if len(parts) == 3 else raw_text
        else:
            speech_body = raw_text

        clean_text, stats = TextCleaner.clean(speech_body)
        quality = TextCleaner.estimate_quality(clean_text)

        # Metadados e contexto inferidos dinamicamente a partir dos próprios dados do documento/pasta
        # Sem hardcoding de nomes específicos de corpus
        collection_name = raw_path.name
        doc_record = {
            "document_id": doc_id,
            "collection": collection_name,
            "doc_type": row.get("tipo_discurso", "discurso"),
            "title": f"Pronunciamento de {row.get('presidente', 'Autor')} ({row.get('ano', '')})",
            "date": str(row.get("ano", "")),
            "author": row.get("presidente", "Desconhecido"),
            "page_count": 1,
            "ocr_quality_overall": quality,
            "archival_context": f"Acervo documental da coleção {collection_name}",
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
