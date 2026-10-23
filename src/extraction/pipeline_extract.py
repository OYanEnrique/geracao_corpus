"""Pipeline de extração atômica de evidências documentais ricas."""
import json
from pathlib import Path
from typing import Dict, Any, List

from src.utils.llm_client import UnifiedLLMClient
from src.utils.config import get_models_config
from src.validation.schema_validator import SchemaValidator


def run_evidence_extraction(sample_chunks_per_doc: int = 1) -> Dict[str, Any]:
    print("=== [Pipeline] Extração de Unidades de Evidência Substantivas ===")
    
    models_cfg = get_models_config()
    gen_cfg = models_cfg["llm_generator"]

    llm = UnifiedLLMClient(
        provider=gen_cfg["provider"],
        model=gen_cfg["model"],
        temperature=gen_cfg["temperature"]
    )
    validator = SchemaValidator()

    with open("prompts/evidence_extraction.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Carregar documentos
    docs_map = {}
    with open("corpus/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            docs_map[d["document_id"]] = d

    # Carregar chunks
    chunks_by_doc: Dict[str, List[Dict[str, Any]]] = {}
    with open("corpus/chunks.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            doc_id = c["document_id"]
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = []
            chunks_by_doc[doc_id].append(c)

    evidences_list: List[Dict[str, Any]] = []
    evidence_counter = 1

    print(f"Extraindo evidências substantivas dos {len(chunks_by_doc)} documentos...")

    for doc_id, doc_chunks in chunks_by_doc.items():
        doc_meta = docs_map.get(doc_id, {})
        # Seleciona trecho temático substantivo (pulando o vocativo cerimonial inicial)
        selected_indices = []
        if len(doc_chunks) > 1:
            selected_indices.append(1)
        else:
            selected_indices.append(0)

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

            # Adicionar diretriz anti-tautologia
            prompt += "\n\nIMPORTANTE: Extraia APENAS afirmações com dados, medidas concretas, diagnósticos socioeconômicos ou fatos específicos. Ignore saudações e frases genéricas."

            response = llm.call_json(prompt)
            if not isinstance(response, list):
                response = [response] if isinstance(response, dict) else []

            for item in response:
                if not isinstance(item, dict) or "claim" not in item:
                    continue

                claim_text = item.get("claim", "").strip()
                # Filtrar claims excessivamente curtas ou tautológicas
                if len(claim_text) < 25:
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
                    "text": item.get("evidence_span", chunk["text"][:200]),
                    "claim": claim_text,
                    "entities": item.get("entities", []) or [doc_meta.get("author", "Governo")],
                    "dates": item.get("dates", []) or [str(doc_meta.get("date", "1985"))],
                    "relations": item.get("relations", []),
                    "evidence_type": item.get("evidence_type", "explicit"),
                    "ocr_quality": chunk.get("ocr_quality", "good"),
                    "notes": item.get("notes", "Extração substantiva") or "Extração substantiva"
                }

                is_valid, errors = validator.validate("evidence", evidence_record)
                if not is_valid:
                    # Pequeno ajuste de saneamento se houver nulos
                    if "notes" in evidence_record and evidence_record["notes"] is None:
                        evidence_record["notes"] = ""
                    is_valid, errors = validator.validate("evidence", evidence_record)

                if is_valid:
                    evidences_list.append(evidence_record)
                else:
                    print(f"  [Aviso Schema {ev_id}]: {errors}")

    output_file = Path("corpus/evidences.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for ev in evidences_list:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    print(f"[OK] Extração concluída: {len(evidences_list)} evidências salvas em {output_file}")
    return {"evidences_count": len(evidences_list), "evidences_path": str(output_file)}


if __name__ == "__main__":
    run_evidence_extraction()
