"""Pipeline de extração atômica de evidências documentais ricas."""
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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

    import concurrent.futures

    tasks = []
    for doc_id, doc_chunks in chunks_by_doc.items():
        doc_meta = docs_map.get(doc_id, {})
        # Seleciona trecho temático substantivo (pulando o vocativo cerimonial inicial se possível)
        chunk = doc_chunks[min(1, len(doc_chunks) - 1)]
        tasks.append((doc_meta, chunk))

    def extract_single(meta, chunk):
        p = (
            prompt_template
            .replace("{document_id}", str(chunk["document_id"]))
            .replace("{chunk_id}", str(chunk["chunk_id"]))
            .replace("{page}", str(chunk["page"]))
            .replace("{date}", str(meta.get("date", "Desconhecido")))
            .replace("{author}", str(meta.get("author", "Desconhecido")))
            .replace("{text}", str(chunk["text"]))
        )
        p += "\n\nIMPORTANTE: Extraia APENAS afirmações com dados, medidas concretas, diagnósticos socioeconômicos ou fatos específicos. Ignore saudações e frases genéricas."
        res = llm.call_json(p)
        if not isinstance(res, list):
            res = [res] if isinstance(res, dict) else []
        return chunk, meta, res

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(extract_single, meta, chunk) for meta, chunk in tasks]
        done_count = 0
        total_tasks = len(tasks)
        for fut in concurrent.futures.as_completed(futures):
            done_count += 1
            if done_count % 10 == 0 or done_count == total_tasks:
                print(f"  Progresso extração: {done_count}/{total_tasks} documentos processados...")
            try:
                chunk, doc_meta, response = fut.result()
                for item in response:
                    if not isinstance(item, dict) or "claim" not in item:
                        continue
                    claim_text = item.get("claim", "").strip()
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
                        "dates": item.get("dates", []) or [str(doc_meta.get("date", "1789"))],
                        "relations": item.get("relations", []),
                        "evidence_type": item.get("evidence_type", "explicit"),
                        "ocr_quality": chunk.get("ocr_quality", "good"),
                        "notes": item.get("notes", "Extração substantiva") or "Extração substantiva"
                    }

                    is_valid, errors = validator.validate("evidence", evidence_record)
                    if not is_valid:
                        if "notes" in evidence_record and evidence_record["notes"] is None:
                            evidence_record["notes"] = ""
                        is_valid, errors = validator.validate("evidence", evidence_record)

                    if is_valid:
                        evidences_list.append(evidence_record)
            except Exception as e:
                print(f"[Aviso Extração]: {e}")

    output_file = Path("corpus/evidences.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for ev in evidences_list:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    print(f"[OK] Extração concluída: {len(evidences_list)} evidências salvas em {output_file}")
    return {"evidences_count": len(evidences_list), "evidences_path": str(output_file)}


if __name__ == "__main__":
    run_evidence_extraction()
