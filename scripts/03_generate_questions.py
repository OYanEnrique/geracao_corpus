import json
import yaml
from pathlib import Path
from utils.llm_client import UnifiedLLMClient


def generate_questions():
    print("=== [Etapa 4] Geração de Perguntas com LLM Ancorada em Evidências ===")

    with open("config/models.yaml", "r", encoding="utf-8") as f:
        models_cfg = yaml.safe_load(f)
    gen_cfg = models_cfg["llm_generator"]

    llm = UnifiedLLMClient(
        provider=gen_cfg["provider"],
        model=gen_cfg["model"],
        temperature=gen_cfg["temperature"]
    )

    # Carregar evidências
    evidences = []
    with open("corpus/evidences.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            evidences.append(json.loads(line))

    # Carregar documentos
    docs_map = {}
    with open("corpus/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            docs_map[d["document_id"]] = d

    # Agrupar evidências por documento
    ev_by_doc = {}
    for ev in evidences:
        doc_id = ev["document_id"]
        if doc_id not in ev_by_doc:
            ev_by_doc[doc_id] = []
        ev_by_doc[doc_id].append(ev)

    questions = []
    q_counter = 1

    # 1. Estratégia 1: Perguntas geradas pelo LLM para evidências individuais
    print("1/3 Gerando perguntas temáticas para evidências single-document...")
    for doc_id, ev_list in ev_by_doc.items():
        doc_meta = docs_map.get(doc_id, {})
        pres = doc_meta.get("author", "o Presidente")
        ano = doc_meta.get("date", "")

        # Selecionar até 2 evidências substantivas por documento
        substantive_evs = [e for e in ev_list if len(e.get("claim", "")) > 40][:2]

        for ev in substantive_evs:
            prompt = f"""Você é um pesquisador em Humanidades Digitais formulando perguntas para um benchmark de RAG verificável.
Com base no fato histórico documental abaixo:
- Documento: Pronunciamento de {pres} ({ano})
- Fato documentado: "{ev['claim']}"
- Trecho literal: "{ev['text'][:250]}"

Formule UMA pergunta de pesquisa em português que investigue especificamente esse fato e que possa ser respondida a partir dele.
Retorne um JSON com o seguinte formato:
{{
  "question": "texto da pergunta",
  "primary_type": "factual ou descriptive ou temporal",
  "reasoning": "lookup",
  "difficulty": "easy ou medium"
}}"""
            res = llm.call_json(prompt)
            if isinstance(res, dict) and "question" in res:
                q_text = res["question"]
                p_type = res.get("primary_type", "factual")
                q_id = f"Q{q_counter:03d}"
                q_counter += 1
                questions.append({
                    "id": q_id,
                    "question": q_text,
                    "primary_type": p_type,
                    "reasoning": res.get("reasoning", "lookup"),
                    "source_type": "single_document",
                    "answerability": "answerable",
                    "required_evidence_ids": [ev["evidence_id"]],
                    "required_documents": 1,
                    "temporal_scope": str(ano),
                    "ocr_quality": ev.get("ocr_quality", "good"),
                    "lexical_distance": "medium",
                    "difficulty": res.get("difficulty", "medium")
                })

    # 2. Estratégia 2: Perguntas Multi-Documento / Comparativas
    print("2/3 Gerando perguntas multi-documento com o LLM...")
    pairs = [
        ("DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR"),
        ("DISCURSO_1995_FHC", "DISCURSO_1999_FHC"),
        ("DISCURSO_2003_LULA", "DISCURSO_2007_LULA"),
        ("DISCURSO_2011_DILMA", "DISCURSO_2015_DILMA"),
        ("DISCURSO_2016_TEMER", "DISCURSO_2019_BOLSONARO"),
        ("DISCURSO_1985_SARNEY", "DISCURSO_2023_LULA")
    ]

    for d1, d2 in pairs:
        if d1 in ev_by_doc and d2 in ev_by_doc and ev_by_doc[d1] and ev_by_doc[d2]:
            ev1 = ev_by_doc[d1][0]
            ev2 = ev_by_doc[d2][0]
            m1 = docs_map.get(d1, {})
            m2 = docs_map.get(d2, {})

            prompt = f"""Você é um historiador formulando uma pergunta de pesquisa comparativa para um benchmark de RAG histórico.
Temos duas evidências de documentos distintos:
- Documento 1 ({m1.get('author')}, {m1.get('date')}): "{ev1['claim']}"
- Documento 2 ({m2.get('author')}, {m2.get('date')}): "{ev2['claim']}"

Crie UMA pergunta comparativa em linguagem natural que exija consultar ambos os documentos para uma resposta completa.
Retorne um JSON:
{{
  "question": "pergunta comparativa em portugues",
  "difficulty": "hard"
}}"""
            res = llm.call_json(prompt)
            if isinstance(res, dict) and "question" in res:
                q_id = f"Q{q_counter:03d}"
                q_counter += 1
                questions.append({
                    "id": q_id,
                    "question": res["question"],
                    "primary_type": "comparative",
                    "reasoning": "comparison",
                    "source_type": "multi_document",
                    "answerability": "answerable",
                    "required_evidence_ids": [ev1["evidence_id"], ev2["evidence_id"]],
                    "required_documents": 2,
                    "temporal_scope": f"{m1.get('date')}-{m2.get('date')}",
                    "ocr_quality": "good",
                    "lexical_distance": "high",
                    "difficulty": "hard"
                })

    # 3. Estratégia 3: Perguntas Adversariais e de Abstenção
    print("3/3 Configurando perguntas de abstenção (unanswerable)...")
    adversarial_cases = [
        {
            "question": "Qual foi a taxa exata de desemprego apurada pelo IBGE no terceiro trimestre de 1987 segundo o discurso de posse de 1985?",
            "temporal_scope": "1987",
            "reasoning": "temporal"
        },
        {
            "question": "Quais ministros de Estado foram formalmente exonerados por decreto durante a sessão de posse de 1990?",
            "temporal_scope": "1990",
            "reasoning": "lookup"
        },
        {
            "question": "Qual foi a avaliação confidencial privada do presidente sobre seus adversários que não foi lida na solenidade de 2003?",
            "temporal_scope": "2003",
            "reasoning": "relation"
        },
        {
            "question": "Quantos votos favoráveis cada partido da oposição deu à emenda constitucional referida no pronunciamento de 2016?",
            "temporal_scope": "2016",
            "reasoning": "aggregation"
        }
    ]

    for adv in adversarial_cases:
        q_id = f"Q{q_counter:03d}"
        q_counter += 1
        questions.append({
            "id": q_id,
            "question": adv["question"],
            "primary_type": "factual",
            "reasoning": adv["reasoning"],
            "source_type": "single_document",
            "answerability": "unanswerable",
            "required_evidence_ids": [],
            "required_documents": 0,
            "temporal_scope": adv["temporal_scope"],
            "ocr_quality": "good",
            "lexical_distance": "high",
            "difficulty": "hard"
        })

    output_file = Path("corpus/questions_draft.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"[OK] Total de perguntas geradas com o LLM: {len(questions)}")
    print(f"  - Arquivo salvo em: {output_file}")


if __name__ == "__main__":
    generate_questions()
