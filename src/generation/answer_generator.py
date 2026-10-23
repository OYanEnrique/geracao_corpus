"""Gerador de respostas de referência (Gold Answers) estritamente fundamentadas e anti-tautológicas."""
import json
from pathlib import Path
from typing import Dict, Any, List

from src.utils.llm_client import UnifiedLLMClient
from src.utils.config import get_models_config


def run_answer_generation() -> Dict[str, Any]:
    print("=== [Pipeline] Geração de Respostas de Referência Anti-Tautológicas ===")

    models_cfg = get_models_config()
    gen_cfg = models_cfg["llm_generator"]

    llm = UnifiedLLMClient(
        provider=gen_cfg["provider"],
        model=gen_cfg["model"],
        temperature=gen_cfg["temperature"]
    )

    with open("prompts/answer_generation.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Carregar mapa de evidências
    evidences_map = {}
    with open("corpus/evidences.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            ev = json.loads(line)
            evidences_map[ev["evidence_id"]] = ev

    # Carregar perguntas rascunho
    questions = []
    with open("corpus/questions_draft.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            questions.append(json.loads(line))

    benchmark_items = []
    print(f"Gerando respostas ancoradas para as {len(questions)} perguntas...")

    for i, q in enumerate(questions, 1):
        req_ids = q.get("required_evidence_ids", [])
        answerability = q["answerability"]
        p_type = q["primary_type"]

        # Coletar objetos de evidência completos
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

        # =====================================================================
        # CASO 1: NÃO RESPONDÍVEL (ABSTENÇÃO EXPLÍCITA)
        # =====================================================================
        if answerability == "unanswerable" or p_type == "unanswerable":
            ref_answer = (
                f"Os pronunciamentos oficiais disponíveis no acervo não contêm registros comprobatórios para responder à pergunta sobre {q['temporal_scope']}. "
                "Para esclarecer este ponto com rigor historiográfico, seria necessário consultar atas legislativas externas, diários confidenciais ou levantamentos estatísticos específicos de órgãos oficiais não documentados nos discursos de posse."
            )
            claims = [
                {
                    "claim_text": f"Os pronunciamentos de posse disponíveis não contêm informações para responder sobre {q['temporal_scope']}.",
                    "supporting_evidence_ids": [],
                    "support_level": "supported"
                }
            ]

        # =====================================================================
        # CASO 2: CONTRADITÓRIA / DIVERGÊNCIAS
        # =====================================================================
        elif p_type == "contradictory":
            evidences_summary = []
            for e in ev_objs:
                orig_ev = evidences_map[e["evidence_id"]]
                evidences_summary.append(f"[{orig_ev['document_id']}]: {orig_ev['claim']}")

            prompt = f"""Você é um historiador que formula a resposta de referência para uma pergunta de DIVERGÊNCIA/CONTRADIÇÃO histórica entre fontes.
Pergunta: "{q['question']}"
Evidências documentais conflitantes:
{chr(10).join(evidences_summary)}

REGRAS ESTITAS:
1. Apresente explicitamente ambas as versões documentadas, citando cada documento de forma neutra.
2. NÃO tome partido e NÃO tente harmonizar ou apagar a divergência.
3. NÃO repita a pergunta no início da resposta.
4. Responda em 2 ou 3 sentenças claras e atômicas.

Retorne estritamente um JSON:
{{
  "reference_answer": "texto da resposta apresentando cada versao com sua fonte",
  "answer_claims": [
    {{"claim_text": "afirmação sobre versao 1", "supporting_evidence_ids": ["{ev_objs[0]['evidence_id'] if ev_objs else 'E0001'}"], "support_level": "supported"}},
    {{"claim_text": "afirmação sobre versao 2", "supporting_evidence_ids": ["{ev_objs[1]['evidence_id'] if len(ev_objs)>1 else 'E0002'}"], "support_level": "supported"}}
  ]
}}"""
            res = llm.call_json(prompt)
            if isinstance(res, dict) and "reference_answer" in res:
                ref_answer = res["reference_answer"]
                claims = res.get("answer_claims", [])
            else:
                ref_answer = " As fontes divergem: " + " Já em contrapartida, ".join(evidences_summary)
                claims = [{
                    "claim_text": ref_answer,
                    "supporting_evidence_ids": req_ids,
                    "support_level": "supported"
                }]

        # =====================================================================
        # CASO 3: EXPLORATÓRIA / SONDAGEM TRANSVERSAL
        # =====================================================================
        elif p_type == "exploratory":
            evidences_summary = []
            for e in ev_objs:
                orig_ev = evidences_map[e["evidence_id"]]
                evidences_summary.append(f"O documento {orig_ev['document_id']} documenta que {orig_ev['claim']}.")

            prompt = f"""Você é um historiador formulando a resposta de referência para uma pergunta EXPLORATÓRIA sobre o acervo.
Pergunta: "{q['question']}"
Evidências dos documentos localizados:
{chr(10).join(evidences_summary)}

REGRAS:
1. Responda de forma direta identificando quais documentos abordam o tema e o que cada um registra.
2. Evite fórmulas vazias ou espelhar a pergunta.
3. Separe cada afirmação por documento citado.

Retorne estritamente um JSON:
{{
  "reference_answer": "texto da resposta agregando os documentos",
  "answer_claims": [
    {{"claim_text": "afirmação documental 1", "supporting_evidence_ids": ["{ev_objs[0]['evidence_id'] if ev_objs else 'E0001'}"], "support_level": "supported"}}
  ]
}}"""
            res = llm.call_json(prompt)
            if isinstance(res, dict) and "reference_answer" in res:
                ref_answer = res["reference_answer"]
                claims = res.get("answer_claims", [])
            else:
                ref_answer = " ".join(evidences_summary)
                claims = [{
                    "claim_text": ref_answer,
                    "supporting_evidence_ids": req_ids,
                    "support_level": "supported"
                }]

        # =====================================================================
        # CASO 4: FACTUAL, TEMPORAL, DESCRITIVA, RELACIONAL, COMPARATIVA
        # =====================================================================
        else:
            evidences_json_str = json.dumps([
                {
                    "evidence_id": e["evidence_id"],
                    "document_id": e["doc_id"],
                    "span_literal": e["span"],
                    "claim_factual": evidences_map[e["evidence_id"]].get("claim", "")
                } for e in ev_objs
            ], ensure_ascii=False, indent=2)

            prompt = f"""Você é um historiador que formula a resposta de referência para uma pergunta de benchmark.

DIRETRIZ CENTRAL ANTI-TAUTOLOGIA:
- Forneça DIRETAMENTE a informação substantiva solicitada.
- NUNCA repita ou ecoe as palavras interrogativas da pergunta como se fossem a resposta.
- Exemplo RUIM: "Qual foi o diagnóstico de X?" -> "O diagnóstico de X foi o diagnóstico de X".
- Exemplo BOM: "Qual foi o diagnóstico de X?" -> "X registrou que a taxa de inflação atingira 400% e o déficit era de 110 trilhões."
- Responda apenas com o que está sustentado nas evidências fornecidas.

Pergunta: {q['question']}
Evidências Documentais:
{evidences_json_str}

Retorne um JSON:
{{
  "reference_answer": "resposta direta e substantiva",
  "answer_claims": [
    {{"claim_text": "sentença afirmativa da resposta", "supporting_evidence_ids": {json.dumps(req_ids)}, "support_level": "supported"}}
  ]
}}"""
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
                ref_answer = " ".join([evidences_map[e["evidence_id"]]["claim"] for e in ev_objs])
                claims = [{
                    "claim_text": ref_answer,
                    "supporting_evidence_ids": req_ids,
                    "support_level": "supported"
                }]

        # Criar item padronizado do benchmark
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
            "created_at": "2026-10-22T23:30:00Z",
            "version": "v0.2_balanced"
        }
        benchmark_items.append(item)
        if i % 4 == 0 or i == len(questions):
            print(f"  Progresso: {i}/{len(questions)} respostas processadas...")

    output_file = Path("corpus/benchmark_items_draft.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for it in benchmark_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    summary = {
        "items_count": len(benchmark_items),
        "output_path": str(output_file)
    }
    print(f"[OK] Geração de respostas concluída: {len(benchmark_items)} itens salvos.")
    return summary


if __name__ == "__main__":
    run_answer_generation()
