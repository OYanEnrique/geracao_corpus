"""Gerador equilibrado de perguntas ancoradas em evidências para todas as 8 categorias do guia."""
import json
from pathlib import Path
from typing import Dict, Any, List

from src.utils.llm_client import UnifiedLLMClient
from src.utils.config import get_models_config


def run_question_generation(target_per_category: int = 4) -> Dict[str, Any]:
    print(f"=== [Pipeline] Geração Equilibrada de Perguntas ({target_per_category} por categoria) ===")

    models_cfg = get_models_config()
    gen_cfg = models_cfg["llm_generator"]

    llm = UnifiedLLMClient(
        provider=gen_cfg["provider"],
        model=gen_cfg["model"],
        temperature=gen_cfg["temperature"]
    )

    # 1. Carregar evidências
    evidences = []
    with open("corpus/evidences.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            evidences.append(json.loads(line))

    # 2. Carregar documentos
    docs_map = {}
    with open("corpus/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            docs_map[d["document_id"]] = d

    # Agrupar evidências por documento
    ev_by_doc: Dict[str, List[Dict[str, Any]]] = {}
    for ev in evidences:
        doc_id = ev["document_id"]
        if doc_id not in ev_by_doc:
            ev_by_doc[doc_id] = []
        ev_by_doc[doc_id].append(ev)

    questions: List[Dict[str, Any]] = []
    q_counter = 1

    # Regras anti-tautologia padrão
    anti_tautology_rule = (
        "DIRETRIZ ANTI-TAUTOLOGIA: A pergunta NUNCA deve entregar a resposta no próprio enunciado. "
        "Não faça perguntas cuja única resposta seja papaguear o texto da pergunta. "
        "Formule uma pergunta de investigação substantiva com boa distância lexical."
    )

    # =========================================================================
    # CATEGORIA 1: FACTUAL (4 itens)
    # =========================================================================
    print("1/8 Gerando perguntas FACTUAIS...")
    factual_docs = ["DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "DISCURSO_1995_FHC", "DISCURSO_2003_LULA"]
    for doc_id in factual_docs[:target_per_category]:
        ev_list = ev_by_doc.get(doc_id, [])
        if not ev_list:
            continue
        ev = ev_list[0]
        meta = docs_map.get(doc_id, {})
        prompt = f"""Você é um historiador formulando perguntas factuais para avaliar um sistema RAG.
{anti_tautology_rule}
Documento: {meta.get('title')} ({meta.get('date')})
Fato documentado: "{ev['claim']}"
Trecho literal: "{ev['text'][:300]}"

Crie UMA pergunta factual direta sobre a informação documentada (ex.: qual valor, qual cargo, qual instituição, qual fato concreto).
Retorne estritamente um JSON:
{{
  "question": "texto da pergunta factual"
}}"""
        res = llm.call_json(prompt)
        q_text = res.get("question", f"Qual fato concreto sobre a situação institucional foi registrado em {meta.get('date')}?")
        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": q_text,
            "primary_type": "factual",
            "reasoning": "lookup",
            "source_type": "single_document",
            "answerability": "answerable",
            "required_evidence_ids": [ev["evidence_id"]],
            "required_documents": 1,
            "temporal_scope": str(meta.get("date", "1985")),
            "ocr_quality": ev.get("ocr_quality", "good"),
            "lexical_distance": "medium",
            "difficulty": "easy"
        })
        q_counter += 1

    # =========================================================================
    # CATEGORIA 2: TEMPORAL (4 itens)
    # =========================================================================
    print("2/8 Gerando perguntas TEMPORAIS...")
    temporal_docs = ["DISCURSO_1985_SARNEY", "DISCURSO_1992_ITAMAR", "DISCURSO_1999_FHC", "DISCURSO_2007_LULA"]
    for doc_id in temporal_docs[:target_per_category]:
        ev_list = ev_by_doc.get(doc_id, [])
        ev = ev_list[min(1, len(ev_list)-1)] if ev_list else None
        if not ev:
            continue
        meta = docs_map.get(doc_id, {})
        prompt = f"""Você é um historiador formulando perguntas temporais para avaliar um sistema RAG.
{anti_tautology_rule}
Documento: {meta.get('title')} ({meta.get('date')})
Evidência: "{ev['claim']}"
Trecho literal: "{ev['text'][:300]}"

Crie UMA pergunta que investigue a dimensão temporal, datas, períodos ou marcos cronológicos associados a esse fato.
Retorne JSON:
{{
  "question": "texto da pergunta temporal"
}}"""
        res = llm.call_json(prompt)
        q_text = res.get("question", f"Em que momento histórico ou período o pronunciamento de {meta.get('date')} situa o acontecimento?")
        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": q_text,
            "primary_type": "temporal",
            "reasoning": "temporal",
            "source_type": "single_document",
            "answerability": "answerable",
            "required_evidence_ids": [ev["evidence_id"]],
            "required_documents": 1,
            "temporal_scope": str(meta.get("date", "1985")),
            "ocr_quality": ev.get("ocr_quality", "good"),
            "lexical_distance": "medium",
            "difficulty": "medium"
        })
        q_counter += 1

    # =========================================================================
    # CATEGORIA 3: DESCRITIVA (4 itens)
    # =========================================================================
    print("3/8 Gerando perguntas DESCRITIVAS...")
    desc_docs = ["DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "DISCURSO_1992_ITAMAR", "DISCURSO_2016_TEMER"]
    for doc_id in desc_docs[:target_per_category]:
        ev_list = ev_by_doc.get(doc_id, [])
        ev = ev_list[min(2, len(ev_list)-1)] if ev_list else None
        if not ev:
            continue
        meta = docs_map.get(doc_id, {})
        prompt = f"""Você é um historiador formulando perguntas descritivas para avaliar um sistema RAG.
{anti_tautology_rule}
Documento: {meta.get('title')} ({meta.get('date')})
Evidência: "{ev['claim']}"
Trecho literal: "{ev['text'][:300]}"

Crie UMA pergunta descritiva sobre o diagnóstico, a gravidade dos problemas ou a caracterização das condições sociais/econômicas.
Retorne JSON:
{{
  "question": "texto da pergunta descritiva"
}}"""
        res = llm.call_json(prompt)
        q_text = res.get("question", f"Como o pronunciamento de {meta.get('date')} descreve a situação e os principais obstáculos enfrentados?")
        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": q_text,
            "primary_type": "descriptive",
            "reasoning": "lookup",
            "source_type": "single_document",
            "answerability": "answerable",
            "required_evidence_ids": [ev["evidence_id"]],
            "required_documents": 1,
            "temporal_scope": str(meta.get("date", "1985")),
            "ocr_quality": ev.get("ocr_quality", "good"),
            "lexical_distance": "medium",
            "difficulty": "medium"
        })
        q_counter += 1

    # =========================================================================
    # CATEGORIA 4: RELACIONAL (4 itens)
    # =========================================================================
    print("4/8 Gerando perguntas RELACIONAIS...")
    rel_docs = ["DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "DISCURSO_2003_LULA", "DISCURSO_2011_DILMA"]
    for doc_id in rel_docs[:target_per_category]:
        ev_list = ev_by_doc.get(doc_id, [])
        ev = ev_list[min(1, len(ev_list)-1)] if ev_list else None
        if not ev:
            continue
        meta = docs_map.get(doc_id, {})
        prompt = f"""Você é um historiador formulando perguntas relacionais para avaliar um sistema RAG.
{anti_tautology_rule}
Documento: {meta.get('title')} ({meta.get('date')})
Evidência: "{ev['claim']}"
Trecho literal: "{ev['text'][:300]}"

Crie UMA pergunta que investigue relações entre pessoas, instituições, cargos, poderes da República ou grupos sociais no trecho.
Retorne JSON:
{{
  "question": "texto da pergunta relacional"
}}"""
        res = llm.call_json(prompt)
        q_text = res.get("question", f"Qual vínculo institucional ou relação com outros poderes foi estabelecido no pronunciamento de {meta.get('date')}?")
        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": q_text,
            "primary_type": "relational",
            "reasoning": "relation",
            "source_type": "single_document",
            "answerability": "answerable",
            "required_evidence_ids": [ev["evidence_id"]],
            "required_documents": 1,
            "temporal_scope": str(meta.get("date", "1985")),
            "ocr_quality": ev.get("ocr_quality", "good"),
            "lexical_distance": "medium",
            "difficulty": "medium"
        })
        q_counter += 1

    # =========================================================================
    # CATEGORIA 5: COMPARATIVA (MULTI-DOCUMENTO) (4 itens)
    # =========================================================================
    print("5/8 Gerando perguntas COMPARATIVAS (Multi-documento)...")
    comp_pairs = [
        ("DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR"),
        ("DISCURSO_1995_FHC", "DISCURSO_2003_LULA"),
        ("DISCURSO_2003_LULA", "DISCURSO_2007_LULA"),
        ("DISCURSO_2016_TEMER", "DISCURSO_2019_BOLSONARO")
    ]
    for d1, d2 in comp_pairs[:target_per_category]:
        ev1 = ev_by_doc[d1][0] if d1 in ev_by_doc and ev_by_doc[d1] else None
        ev2 = ev_by_doc[d2][0] if d2 in ev_by_doc and ev_by_doc[d2] else None
        if not ev1 or not ev2:
            continue
        m1 = docs_map.get(d1, {})
        m2 = docs_map.get(d2, {})
        prompt = f"""Você é um historiador formulando perguntas comparativas multi-documento.
{anti_tautology_rule}
Documento 1 ({m1.get('author')}, {m1.get('date')}): "{ev1['claim']}"
Documento 2 ({m2.get('author')}, {m2.get('date')}): "{ev2['claim']}"

Crie UMA pergunta comparativa em linguagem natural que exija confrontar ambos os discursos para ser respondida.
Retorne JSON:
{{
  "question": "texto da pergunta comparativa"
}}"""
        res = llm.call_json(prompt)
        q_text = res.get("question", f"Como os pronunciamentos de {m1.get('author')} ({m1.get('date')}) e {m2.get('author')} ({m2.get('date')}) diferem quanto às prioridades iniciais de governo?")
        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": q_text,
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
        q_counter += 1

    # =========================================================================
    # CATEGORIA 6: EXPLORATÓRIA (4 itens)
    # =========================================================================
    print("6/8 Gerando perguntas EXPLORATÓRIAS (Transversais no acervo)...")
    # Perguntas que sondam temas transversais cobrindo múltiplos documentos do acervo
    exploratory_themes = [
        {
            "theme": "diagnóstico da dívida e desordem fiscal",
            "docs": ["DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "DISCURSO_1992_ITAMAR"],
            "question": "Quais pronunciamentos de posse abordam explicitamente a crise das contas públicas, o endividamento e a desordem fiscal do Estado?"
        },
        {
            "theme": "assistência social e combate à fome e pobreza",
            "docs": ["DISCURSO_1985_SARNEY", "DISCURSO_1992_ITAMAR", "DISCURSO_2003_LULA"],
            "question": "Quais documentos do acervo apontam a superação da fome e da miséria como dever moral e prioridade central de governo?"
        },
        {
            "theme": "compromisso com a democracia e respeito ao Congresso",
            "docs": ["DISCURSO_1985_SARNEY", "DISCURSO_1995_FHC", "DISCURSO_2007_LULA"],
            "question": "Quais discursos de posse destacam expressamente a conciliação entre os Poderes e o respeito à representação parlamentar do Congresso Nacional?"
        },
        {
            "theme": "papel do Estado e reformas institucionais",
            "docs": ["DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "DISCURSO_2016_TEMER"],
            "question": "Quais pronunciamentos oficiais do acervo defendem medidas emergenciais de reformas e contenção de gastos públicos?"
        }
    ]

    for item in exploratory_themes[:target_per_category]:
        # Coletar evidências dos documentos mapeados
        req_eids = []
        for d in item["docs"]:
            if d in ev_by_doc and ev_by_doc[d]:
                req_eids.append(ev_by_doc[d][0]["evidence_id"])

        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": item["question"],
            "primary_type": "exploratory",
            "reasoning": "aggregation",
            "source_type": "multi_document",
            "answerability": "answerable",
            "required_evidence_ids": req_eids,
            "required_documents": len(req_eids),
            "temporal_scope": "1985-2016",
            "ocr_quality": "good",
            "lexical_distance": "high",
            "difficulty": "hard"
        })
        q_counter += 1

    # =========================================================================
    # CATEGORIA 7: CONTRADITÓRIA / DIVERGÊNCIAS (4 itens)
    # =========================================================================
    print("7/8 Gerando perguntas CONTRADITÓRIAS (Divergências historiográficas)...")
    contradictory_cases = [
        {
            "d1": "DISCURSO_1985_SARNEY",
            "d2": "DISCURSO_1990_COLLOR",
            "question": "De que maneiras distintas os discursos de 1985 e 1990 posicionam o papel da presença do Estado e das empresas estatais na crise econômica nacional?",
            "divergence": "Sarney (1985) propõe conciliação nacional com saneamento sem recessão, enquanto Collor (1990) condena duramente a avassaladora presença do Estado como causa direta do atraso."
        },
        {
            "d1": "DISCURSO_1990_COLLOR",
            "d2": "DISCURSO_2003_LULA",
            "question": "Qual é a divergência fundamental expressa nos pronunciamentos de 1990 e 2003 quanto à atuação do mercado e à proteção social frente à modernização econômica?",
            "divergence": "Collor (1990) enfatiza desregulamentação e redução drástica do Estado, ao passo que Lula (2003) sustenta a primazia do combate à fome e a ação estatal compensatória."
        },
        {
            "d1": "DISCURSO_1985_SARNEY",
            "d2": "DISCURSO_1995_FHC",
            "question": "Como os discursos de 1985 e 1995 apresentam visões conflitantes sobre as raízes da inflação e o alcance dos planos de estabilização anteriores?",
            "divergence": "Sarney (1985) aponta a inflação herdada da ditadura como limite estrutural intransponível no curto prazo, enquanto FHC (1995) postula a consolidação do Real superando o ciclo anterior."
        },
        {
            "d1": "DISCURSO_2016_TEMER",
            "d2": "DISCURSO_2019_BOLSONARO",
            "question": "Como a justificativa para a posse e a legitimidade política divergem entre o pronunciamento de 2016 e o de 2019?",
            "divergence": "Temer (2016) ancora a legitimidade na ordem constitucional de salvação nacional e pacificação política, enquanto Bolsonaro (2019) enfatiza ruptura ideológica e desígnio pessoal/religioso."
        }
    ]

    for item in contradictory_cases[:target_per_category]:
        d1, d2 = item["d1"], item["d2"]
        ev1 = ev_by_doc[d1][0] if d1 in ev_by_doc and ev_by_doc[d1] else None
        ev2 = ev_by_doc[d2][0] if d2 in ev_by_doc and ev_by_doc[d2] else None
        req_eids = [e["evidence_id"] for e in [ev1, ev2] if e]
        m1 = docs_map.get(d1, {})
        m2 = docs_map.get(d2, {})

        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": item["question"],
            "primary_type": "contradictory",
            "reasoning": "contradiction",
            "source_type": "multi_document",
            "answerability": "answerable",
            "required_evidence_ids": req_eids,
            "required_documents": len(req_eids),
            "temporal_scope": f"{m1.get('date')}-{m2.get('date')}",
            "ocr_quality": "good",
            "lexical_distance": "high",
            "difficulty": "hard"
        })
        q_counter += 1

    # =========================================================================
    # CATEGORIA 8: NÃO RESPONDÍVEL / ABSTENÇÃO (4 itens)
    # =========================================================================
    print("8/8 Configurando perguntas NÃO RESPONDÍVEIS (Abstenção / Adversariais)...")
    unanswerable_cases = [
        {
            "question": "Qual foi a taxa exata de desemprego apurada pelo IBGE no terceiro trimestre de 1987 segundo o discurso de posse de 1985?",
            "temporal_scope": "1987",
            "reasoning": "temporal"
        },
        {
            "question": "Quais ministros de Estado foram formalmente exonerados por decreto durante a sessão solene de posse de 1990?",
            "temporal_scope": "1990",
            "reasoning": "lookup"
        },
        {
            "question": "Qual foi a avaliação confidencial privada do presidente sobre seus adversários que não foi lida na solenidade de 2003?",
            "temporal_scope": "2003",
            "reasoning": "relation"
        },
        {
            "question": "Quantos votos nominais favoráveis cada bancada partidária deu à emenda constitucional referida no pronunciamento de 2016?",
            "temporal_scope": "2016",
            "reasoning": "aggregation"
        }
    ]

    for item in unanswerable_cases[:target_per_category]:
        questions.append({
            "id": f"Q{q_counter:03d}",
            "question": item["question"],
            "primary_type": "unanswerable",
            "reasoning": item["reasoning"],
            "source_type": "single_document",
            "answerability": "unanswerable",
            "required_evidence_ids": [],
            "required_documents": 0,
            "temporal_scope": item["temporal_scope"],
            "ocr_quality": "good",
            "lexical_distance": "high",
            "difficulty": "hard"
        })
        q_counter += 1

    # 3. Salvar perguntas rascunho
    output_file = Path("corpus/questions_draft.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Contabilidade de categorias
    counts_by_cat: Dict[str, int] = {}
    for q in questions:
        cat = q["primary_type"]
        counts_by_cat[cat] = counts_by_cat.get(cat, 0) + 1

    summary = {
        "total_questions": len(questions),
        "target_per_category": target_per_category,
        "counts_by_category": counts_by_cat,
        "percentages_by_category": {cat: f"{(cnt/len(questions))*100:.1f}%" for cat, cnt in counts_by_cat.items()},
        "questions_path": str(output_file)
    }

    print(f"[OK] Geração concluída: {len(questions)} perguntas geradas.")
    for cat, cnt in counts_by_cat.items():
        print(f"  - {cat.upper()}: {cnt} ({summary['percentages_by_category'][cat]})")
    return summary


if __name__ == "__main__":
    run_question_generation()
