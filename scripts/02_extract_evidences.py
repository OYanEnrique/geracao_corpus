import json
import yaml
from pathlib import Path
from utils.llm_client import UnifiedLLMClient
from utils.schema_validator import SchemaValidator


def extract_evidences(sample_chunks_per_doc: int = 1):
    print("=== [Etapa 3] Extração de Unidades de Evidência ===")
    
    with open("config/models.yaml", "r", encoding="utf-8") as f:
        models_cfg = yaml.safe_load(f)
    gen_cfg = models_cfg["llm_generator"]

    llm = UnifiedLLMClient(
        provider=gen_cfg["provider"],
        model=gen_cfg["model"],
        temperature=gen_cfg["temperature"]
    )
    validator = SchemaValidator()

    with open("prompts/evidence_extraction.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Carregar documentos para metadados adicionais
    docs_map = {}
    with open("corpus/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            docs_map[d["document_id"]] = d

    # Carregar chunks
    chunks_by_doc = {}
    with open("corpus/chunks.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            doc_id = c["document_id"]
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = []
            chunks_by_doc[doc_id].append(c)

    evidences_list = []
    evidence_counter = 1

    print(f"Processando amostra de {sample_chunks_per_doc} chunks para cada um dos {len(chunks_by_doc)} documentos...")

    for doc_id, doc_chunks in chunks_by_doc.items():
        doc_meta = docs_map.get(doc_id, {})
        # Amostrar trechos com conteúdo substantivo (evitando o vocativo cerimonial inicial)
        selected_indices = []
        if len(doc_chunks) > 1:
            selected_indices.append(1)
        else:
            selected_indices.append(0)

        if len(doc_chunks) > 3:
            selected_indices.append(len(doc_chunks) // 2)
            selected_indices.append(len(doc_chunks) - 2)
        elif len(doc_chunks) > 2:
            selected_indices.append(len(doc_chunks) - 1)
        selected_indices = sorted(list(set(selected_indices)))[:sample_chunks_per_doc]

        for idx in selected_indices:
            chunk = doc_chunks[idx]
            prompt = (
                prompt_template
                .replace("{document_id}", str(chunk["document_id"]))
                .replace("{chunk_id}", str(chunk["chunk_id"]))
                .replace("{page}", str(chunk["page"]))
                .replace("{date}", str(doc_meta.get("date", "Desconhecido")))
                .replace("{author}", str(doc_meta.get("author", "Desconhecido")))
                .replace("{text}", str(chunk["text"]))
            )

            response = llm.call_json(prompt)
            if not isinstance(response, list):
                response = [response] if isinstance(response, dict) else []

            for item in response:
                if not isinstance(item, dict) or "claim" not in item:
                    continue

                ev_id = f"E{evidence_counter:04d}"
                evidence_counter += 1

                evidence_record = {
                    "evidence_id": ev_id,
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "page": chunk["page"],
                    "char_start": chunk["char_start"],
                    "char_end": chunk["char_end"],
                    "text": item.get("evidence_span", chunk["text"][:150]),
                    "claim": item.get("claim", ""),
                    "entities": item.get("entities", []),
                    "dates": item.get("dates", [doc_meta.get("date", "1985")]),
                    "relations": item.get("relations", []),
                    "evidence_type": item.get("evidence_type", "explicit"),
                    "ocr_quality": chunk.get("ocr_quality", "good"),
                    "notes": item.get("notes", "")
                }

                # Validar schema
                is_valid, errors = validator.validate("evidence", evidence_record)
                if not is_valid:
                    print(f"  [Aviso Schema {ev_id}]: {errors}")
                else:
                    evidences_list.append(evidence_record)

    output_file = Path("corpus/evidences.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for ev in evidences_list:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    print(f"[OK] Extracao concluida com sucesso:")
    print(f"  - Total de evidencias extraidas e validadas: {len(evidences_list)}")
    print(f"  - Arquivo salvo em: {output_file}")


if __name__ == "__main__":
    extract_evidences()
