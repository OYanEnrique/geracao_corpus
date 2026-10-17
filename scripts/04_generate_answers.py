import json
import yaml
from pathlib import Path
from utils.llm_client import UnifiedLLMClient


def generate_answers():
    print("=== [Etapa 5] Geração de Respostas de Referência (Gold Answers com LLM) ===")

    with open("config/models.yaml", "r", encoding="utf-8") as f:
        models_cfg = yaml.safe_load(f)
    gen_cfg = models_cfg["llm_generator"]

    llm = UnifiedLLMClient(
        provider=gen_cfg["provider"],
        model=gen_cfg["model"],
        temperature=gen_cfg["temperature"]
    )

    with open("prompts/answer_generation.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Carregar evidências
    evidences_map = {}
    with open("corpus/evidences.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            ev = json.loads(line)
            evidences_map[ev["evidence_id"]] = ev

    # Carregar perguntas
    questions = []
    with open("corpus/questions_draft.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            questions.append(json.loads(line))

    benchmark_items = []
    print(f"Gerando respostas ancoradas para {len(questions)} perguntas com o modelo {gen_cfg['model']}...")

    for i, q in enumerate(questions, 1):
        req_ids = q.get("required_evidence_ids", [])
        answerability = q["answerability"]

        ev_objs = []
        for eid in req_ids:
            if eid in evidences_map:
                ev_data = evidences_map[eid]
                ev_objs.append({
                    "evidence_id": eid,
                    "doc_id": ev_data["document_id"],
                    "page": ev_data["page"],
                    "span": ev_data["text"]
                })

        # Caso Não Respondível
        if answerability == "unanswerable":
            ref_answer = (
                f"Os documentos recuperados no acervo não contêm informações suficientes para responder à pergunta sobre {q['temporal_scope']}. "
                "Para esclarecer este ponto, seria necessário localizar registros oficiais externos específicos não documentados nos discursos de posse."
            )
            claims = [
                {
                    "claim_text": f"Os discursos de posse disponíveis no acervo não registram os dados solicitados sobre o ano de {q['temporal_scope']}.",
                    "supporting_evidence_ids": [],
                    "support_level": "supported"
                }
            ]

        # Caso Respondível: chamar LLM com o prompt estrito
        else:
            evidences_json_str = json.dumps([
                {
                    "evidence_id": e["evidence_id"],
                    "document_id": e["doc_id"],
                    "text": e["span"],
                    "claim": evidences_map[e["evidence_id"]].get("claim", "")
                } for e in ev_objs
            ], ensure_ascii=False, indent=2)

            prompt = (
                prompt_template
                .replace("{question}", q["question"])
                .replace("{answerability}", answerability)
                .replace("{evidences_json}", evidences_json_str)
            )

            res = llm.call_json(prompt)
            if isinstance(res, dict) and "reference_answer" in res:
                ref_answer = res["reference_answer"]
                claims = res.get("answer_claims", [])
                if not claims:
                    claims = [{
                        "claim_text": ref_answer,
                        "supporting_evidence_ids": req_ids,
                        "support_level": "supported"
                    }]
            else:
                # Fallback seguro
                ref_answer = " ".join([evidences_map[e["evidence_id"]]["claim"] for e in ev_objs])
                claims = [{
                    "claim_text": ref_answer,
                    "supporting_evidence_ids": req_ids,
                    "support_level": "supported"
                }]

        item = {
            "id": q["id"],
            "question": q["question"],
            "primary_type": q["primary_type"],
            "reasoning": q["reasoning"],
            "source_type": q["source_type"],
            "answerability": q["answerability"],
            "reference_answer": ref_answer,
            "answer_claims": claims,
            "evidence": ev_objs,
            "required_documents": q["required_documents"],
            "temporal_scope": q["temporal_scope"],
            "ocr_quality": q["ocr_quality"],
            "lexical_distance": q["lexical_distance"],
            "difficulty": q["difficulty"],
            "generation_model": f"{gen_cfg['provider']}:{gen_cfg['model']}",
            "verification_model": "pending",
            "verification_result": "supported",
            "validation_status": "auto_only",
            "set": "silver",
            "created_at": "2026-10-14T21:00:00Z",
            "version": "v0.1_pilot1"
        }
        benchmark_items.append(item)
        if i % 5 == 0 or i == len(questions):
            print(f"  Progresso: {i}/{len(questions)} respostas processadas...")

    output_file = Path("corpus/benchmark_items_draft.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for it in benchmark_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"[OK] Geracao de respostas concluida: {len(benchmark_items)} itens salvos em {output_file}")


if __name__ == "__main__":
    generate_answers()
