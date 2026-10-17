import csv
import json
from pathlib import Path
from utils.ocr_cleaner import OCRCleaner
from utils.chunker import SentenceWindowChunker
from utils.schema_validator import SchemaValidator


def prepare_documents():
    print("=== [Etapa 1 & 2] Preparação e Segmentação dos Documentos ===")
    raw_dir = Path("data/raw/piloto_1")
    metadata_csv = raw_dir / "metadados_discursos.csv"
    output_dir = Path("corpus")
    output_dir.mkdir(exist_ok=True)

    validator = SchemaValidator()
    chunker = SentenceWindowChunker(target_chars=1200, overlap_chars=200, min_chars=300)

    documents_out = output_dir / "documents.jsonl"
    chunks_out = output_dir / "chunks.jsonl"

    documents_list = []
    chunks_list = []

    with open(metadata_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Lendo {len(rows)} registros de {metadata_csv}...")

    for row in rows:
        doc_id = row["id_doc"]
        filename = row["arquivo_bruto"]
        file_path = raw_dir / filename

        if not file_path.exists():
            print(f"[Aviso] Arquivo não encontrado: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as tf:
            raw_text = tf.read()

        clean_text, stats = OCRCleaner.clean(raw_text)
        quality = OCRCleaner.estimate_quality(clean_text)

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

        # Validação de schema
        is_valid, errors = validator.validate("document", doc_record)
        if not is_valid:
            print(f"[Erro de Schema em {doc_id}]: {errors}")
        else:
            documents_list.append(doc_record)

        # Segmentação do documento
        doc_chunks = chunker.chunk_document(doc_id=doc_id, text=clean_text, page=1)
        for c in doc_chunks:
            c["ocr_quality"] = quality
        chunks_list.extend(doc_chunks)

    # Gravação dos arquivos JSONL
    with open(documents_out, "w", encoding="utf-8") as f:
        for doc in documents_list:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    with open(chunks_out, "w", encoding="utf-8") as f:
        for chunk in chunks_list:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"[OK] Concluido com sucesso:")
    print(f"  - Documentos validos salvos: {len(documents_list)} em {documents_out}")
    print(f"  - Chunks gerados: {len(chunks_list)} em {chunks_out}")


if __name__ == "__main__":
    prepare_documents()
