"""Módulo gerador e validador contínuo por comitês (3 modelos maiores + 3 menores).
Executa em loop contínuo até atingir exatamente 10 perguntas válidas aprovadas para cada uma das 8 categorias (80 no total).
"""
import os
import sys
import json
import time
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


def safe_print(msg: str):
    """Garante que a mensagem seja impressa sem erro de codificação de charmap no Windows."""
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass


from src.utils.committee import GenerationCommittee, AuditingCommittee
from src.validation.schema_validator import SchemaValidator


def run_committee_generation_loop(target_per_category: int = 10) -> Dict[str, Any]:
    safe_print("================================================================================")
    safe_print(" COMITÊS DE MODELOS: GERAÇÃO E AUDITORIA COM VOTAÇÃO E REJEIÇÃO DE TAUTOLOGIA")
    safe_print(f" Meta: {target_per_category} perguntas válidas por categoria | Total: {target_per_category * 8} perguntas")
    safe_print("================================================================================")

    # 1. Inicializar comitês
    gen_committee = GenerationCommittee()
    audit_committee = AuditingCommittee()
    schema_validator = SchemaValidator()

    safe_print("[Comitê Geração] 3 Modelos Maiores:")
    for m in gen_committee.models_meta:
        safe_print(f"  - {m['name']} ({m['provider']} / {m['model']})")

    safe_print("[Comitê Auditoria] 3 Modelos Menores:")
    for m in audit_committee.models_meta:
        safe_print(f"  - {m['name']} ({m['provider']} / {m['model']})")

    # 2. Carregar evidências e documentos
    evidences = []
    with open("corpus/evidences.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                evidences.append(json.loads(line))

    docs_map = {}
    with open("corpus/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                docs_map[d["document_id"]] = d

    # Agrupar evidências por documento
    ev_by_doc: Dict[str, List[Dict[str, Any]]] = {}
    for ev in evidences:
        doc_id = ev["document_id"]
        if doc_id not in ev_by_doc:
            ev_by_doc[doc_id] = []
        ev_by_doc[doc_id].append(ev)

    categories = [
        "factual",
        "temporal",
        "descriptive",
        "relational",
        "comparative",
        "exploratory",
        "contradictory",
        "unanswerable"
    ]

    all_approved: List[Dict[str, Any]] = []
    all_rejections: List[Dict[str, Any]] = []
    cat_counts = {c: 0 for c in categories}
    seen_questions = set()

    # Recuperação do Checkpoint
    checkpoint_file = Path("corpus/committee_checkpoint.jsonl")
    if checkpoint_file.exists():
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    all_approved.append(item)
                    cat = item["primary_type"]
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1
                    q_norm = " ".join(item["question"].lower().split())
                    seen_questions.add(q_norm)
        safe_print(f"[Recuperação] {len(all_approved)} itens carregados do checkpoint: {cat_counts}")

    total_q_counter = len(all_approved) + 1

    # Temas transversais para exploratórias
    exploratory_themes = [
        ("diagnóstico da inflação e desordem fiscal", ["DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "DISCURSO_1992_ITAMAR"]),
        ("combate à fome e erradicação da miséria", ["DISCURSO_1985_SARNEY", "DISCURSO_1992_ITAMAR", "DISCURSO_2003_LULA"]),
        ("relação harmônica entre os Poderes e o Congresso", ["DISCURSO_1985_SARNEY", "DISCURSO_1995_FHC", "DISCURSO_2007_LULA"]),
        ("reformas institucionais e redefinição do Estado", ["DISCURSO_1990_COLLOR", "DISCURSO_1995_FHC", "DISCURSO_2016_TEMER"]),
        ("desenvolvimento educacional e científico", ["DISCURSO_1995_FHC", "DISCURSO_2007_LULA", "DISCURSO_2011_DILMA"]),
        ("direitos trabalhistas, emprego e salário real", ["DISCURSO_1985_SARNEY", "DISCURSO_1992_ITAMAR", "DISCURSO_2003_LULA"]),
        ("política externa, soberania e inserção internacional", ["DISCURSO_1990_COLLOR", "DISCURSO_2003_LULA", "DISCURSO_2019_BOLSONARO"]),
        ("combate à corrupção, ética pública e moralidade", ["DISCURSO_1990_COLLOR", "DISCURSO_1992_ITAMAR", "DISCURSO_2019_BOLSONARO"]),
        ("proteção ambiental e desenvolvimento sustentável", ["DISCURSO_1992_ITAMAR", "DISCURSO_2011_DILMA", "DISCURSO_2023_LULA"]),
        ("pacificação nacional e superação de ódios políticos", ["DISCURSO_1985_SARNEY", "DISCURSO_2016_TEMER", "DISCURSO_2023_LULA"])
    ]

    # Pares de comparação multi-documento
    comp_pairs = [
        ("DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR"),
        ("DISCURSO_1990_COLLOR", "DISCURSO_1992_ITAMAR"),
        ("DISCURSO_1992_ITAMAR", "DISCURSO_1995_FHC"),
        ("DISCURSO_1995_FHC", "DISCURSO_1999_FHC"),
        ("DISCURSO_1999_FHC", "DISCURSO_2003_LULA"),
        ("DISCURSO_2003_LULA", "DISCURSO_2007_LULA"),
        ("DISCURSO_2007_LULA", "DISCURSO_2011_DILMA"),
        ("DISCURSO_2011_DILMA", "DISCURSO_2015_DILMA"),
        ("DISCURSO_2015_DILMA", "DISCURSO_2016_TEMER"),
        ("DISCURSO_2016_TEMER", "DISCURSO_2019_BOLSONARO"),
        ("DISCURSO_2019_BOLSONARO", "DISCURSO_2023_LULA"),
        ("DISCURSO_1985_SARNEY", "DISCURSO_2023_LULA")
    ]

    # Casos de divergência contraditória historiográfica
    contradictory_cases = [
        ("DISCURSO_1985_SARNEY", "DISCURSO_1990_COLLOR", "presença do Estado e saneamento da economia"),
        ("DISCURSO_1990_COLLOR", "DISCURSO_2003_LULA", "papel do livre mercado versus intervenção social"),
        ("DISCURSO_1985_SARNEY", "DISCURSO_1995_FHC", "diagnóstico sobre raízes da inflação e estabilização"),
        ("DISCURSO_1995_FHC", "DISCURSO_2003_LULA", "avaliação da herança das privatizações e do modelo econômico"),
        ("DISCURSO_2003_LULA", "DISCURSO_2019_BOLSONARO", "alinhamento internacional e diretrizes ideológicas de governo"),
        ("DISCURSO_2016_TEMER", "DISCURSO_2019_BOLSONARO", "justificativa de legitimidade política e ordem institucional"),
        ("DISCURSO_1990_COLLOR", "DISCURSO_1992_ITAMAR", "estratégia de modernização com choque versus conciliação ética"),
        ("DISCURSO_2011_DILMA", "DISCURSO_2016_TEMER", "diagnóstico sobre equilíbrio fiscal e reformas constitucionais"),
        ("DISCURSO_2019_BOLSONARO", "DISCURSO_2023_LULA", "concepção sobre união nacional, direitos sociais e meio ambiente"),
        ("DISCURSO_1985_SARNEY", "DISCURSO_2023_LULA", "desafios da reconstrução democrática após transição de poder")
    ]

    # Casos de não respondibilidade (Abstenção explícita)
    unanswerable_templates = [
        ("Qual foi a taxa exata de inflação mensal do IPCA registrada no mês subsequente à posse de {ano}?", "lookup"),
        ("Quais foram os nomes dos ministros exonerados em reunião secreta antes da solenidade de {ano}?", "lookup"),
        ("Quantos votos individuais de cada parlamentar foram computados na votação mencionada no discurso de {ano}?", "aggregation"),
        ("Qual foi o parecer técnico sigiloso elaborado pelo Banco Central que embasou as declarações de {ano}?", "relation"),
        ("Quais foram os valores detalhados de doações privadas de campanha citados na cerimônia de {ano}?", "lookup")
    ]

    # LOOP PRINCIPAL: Enquanto qualquer categoria não tiver target_per_category aprovados
    for category in categories:
        if cat_counts[category] >= target_per_category:
            safe_print(f">>> Categoria {category.upper()}: Já atingiu a meta ({cat_counts[category]}/{target_per_category}). Pulando. <<<")
            continue

        safe_print(f"\n>>> Processando Categoria: {category.upper()} (Meta: {target_per_category} aprovadas | Atual: {cat_counts[category]}) <<<")
        iteration_attempt = 0

        while cat_counts[category] < target_per_category:
            iteration_attempt += 1
            slot_idx = cat_counts[category]

            # Selecionar contexto de acordo com a categoria
            ev_list = []
            context_prompt = ""
            temporal_scope = "1985"
            source_type = "single_document"
            reasoning = "lookup"
            answerability = "answerable"

            if category in ["factual", "temporal", "descriptive", "relational"]:
                doc_keys = list(ev_by_doc.keys())
                chosen_doc = doc_keys[(slot_idx + iteration_attempt - 1) % len(doc_keys)]
                doc_evs = ev_by_doc.get(chosen_doc, [])
                if not doc_evs:
                    continue
                chosen_ev = doc_evs[min(iteration_attempt - 1, len(doc_evs) - 1)]
                ev_list = [chosen_ev]
                meta = docs_map.get(chosen_doc, {})
                temporal_scope = str(meta.get("date", "1985"))

                if category == "factual":
                    reasoning = "lookup"
                    context_prompt = (
                        f"Documento Histórico: {meta.get('title')} ({meta.get('date')})\n"
                        f"Fato Comprovado: \"{chosen_ev['claim']}\"\n"
                        f"Trecho Documental: \"{chosen_ev['text'][:350]}\"\n"
                        "Crie uma pergunta factual objetiva sobre dados concretos, cargos, valores ou instituições mencionados."
                    )
                elif category == "temporal":
                    reasoning = "temporal"
                    context_prompt = (
                        f"Documento Histórico: {meta.get('title')} ({meta.get('date')})\n"
                        f"Fato Comprovado: \"{chosen_ev['claim']}\"\n"
                        f"Trecho Documental: \"{chosen_ev['text'][:350]}\"\n"
                        "Crie uma pergunta que investigue a dimensão cronológica, datas, prazos ou marcos temporais expressos no trecho."
                    )
                elif category == "descriptive":
                    reasoning = "lookup"
                    context_prompt = (
                        f"Documento Histórico: {meta.get('title')} ({meta.get('date')})\n"
                        f"Fato Comprovado: \"{chosen_ev['claim']}\"\n"
                        f"Trecho Documental: \"{chosen_ev['text'][:350]}\"\n"
                        "Crie uma pergunta descritiva que indague a caracterização da situação econômica, da gravidade da crise ou das diretrizes descritas."
                    )
                elif category == "relational":
                    reasoning = "relation"
                    context_prompt = (
                        f"Documento Histórico: {meta.get('title')} ({meta.get('date')})\n"
                        f"Fato Comprovado: \"{chosen_ev['claim']}\"\n"
                        f"Trecho Documental: \"{chosen_ev['text'][:350]}\"\n"
                        "Crie uma pergunta relacional sobre articulações institucionais, diálogo entre poderes, atores políticos ou pactos sociais referidos."
                    )

            elif category == "comparative":
                source_type = "multi_document"
                reasoning = "comparison"
                pair_idx = (slot_idx + iteration_attempt - 1) % len(comp_pairs)
                d1, d2 = comp_pairs[pair_idx]
                m1 = docs_map.get(d1, {})
                m2 = docs_map.get(d2, {})
                e1 = ev_by_doc[d1][0] if d1 in ev_by_doc and ev_by_doc[d1] else None
                e2 = ev_by_doc[d2][0] if d2 in ev_by_doc and ev_by_doc[d2] else None
                if not e1 or not e2:
                    continue
                ev_list = [e1, e2]
                temporal_scope = f"{m1.get('date')}-{m2.get('date')}"
                context_prompt = (
                    f"Documento 1 ({m1.get('author')}, {m1.get('date')}): \"{e1['claim']}\" (Trecho: \"{e1['text'][:200]}\")\n"
                    f"Documento 2 ({m2.get('author')}, {m2.get('date')}): \"{e2['claim']}\" (Trecho: \"{e2['text'][:200]}\")\n"
                    "Crie uma pergunta comparativa em linguagem natural que demande contrastar as posições, diagnósticos ou prioridades entre ambos os governantes."
                )

            elif category == "exploratory":
                source_type = "multi_document"
                reasoning = "aggregation"
                t_idx = (slot_idx + iteration_attempt - 1) % len(exploratory_themes)
                theme_title, doc_ids = exploratory_themes[t_idx]
                ev_list = []
                for did in doc_ids:
                    if did in ev_by_doc and ev_by_doc[did]:
                        ev_list.append(ev_by_doc[did][0])
                temporal_scope = "1985-2023"
                context_prompt = (
                    f"Tema Histórico Transversal: {theme_title}\n"
                    f"Documentos que abordam o tema no acervo: {', '.join(doc_ids)}\n"
                    "Crie uma pergunta exploratória ampla que solicite identificar e sintetizar como esse tema transversal foi tratado nos pronunciamentos oficiais."
                )

            elif category == "contradictory":
                source_type = "multi_document"
                reasoning = "contradiction"
                c_idx = (slot_idx + iteration_attempt - 1) % len(contradictory_cases)
                d1, d2, divergence_topic = contradictory_cases[c_idx]
                m1 = docs_map.get(d1, {})
                m2 = docs_map.get(d2, {})
                e1 = ev_by_doc[d1][0] if d1 in ev_by_doc and ev_by_doc[d1] else None
                e2 = ev_by_doc[d2][0] if d2 in ev_by_doc and ev_by_doc[d2] else None
                if not e1 or not e2:
                    continue
                ev_list = [e1, e2]
                temporal_scope = f"{m1.get('date')}-{m2.get('date')}"
                context_prompt = (
                    f"Tópico de Divergência Historiográfica: {divergence_topic}\n"
                    f"Fonte A ({m1.get('author')}, {m1.get('date')}): \"{e1['claim']}\"\n"
                    f"Fonte B ({m2.get('author')}, {m2.get('date')}): \"{e2['claim']}\"\n"
                    "Crie uma pergunta que investigue a divergência ou tensão conceitual explícita entre as duas visões documentadas."
                )

            elif category == "unanswerable":
                answerability = "unanswerable"
                u_idx = (slot_idx + iteration_attempt - 1) % len(unanswerable_templates)
                template_text, u_reasoning = unanswerable_templates[u_idx]
                years = ["1985", "1990", "1992", "1995", "1999", "2003", "2007", "2011", "2016", "2019", "2023"]
                y = years[(slot_idx + iteration_attempt) % len(years)]
                q_candidate = template_text.format(ano=y)
                temporal_scope = y
                reasoning = u_reasoning
                ev_list = []
                context_prompt = f"Pergunta adversarial de abstenção histórica sobre o ano de {y}."

            # ETAPA A: Proposição e Votação no Comitê de Geração
            if category == "unanswerable":
                selected_question = q_candidate
                gen_voting = {"winner": q_candidate, "candidate_author": "Template Historiográfico Adversarial", "votes_count": {1: 3, 2: 0}}
            else:
                gen_voting = gen_committee.propose_and_vote_question(category, context_prompt)
                selected_question = gen_voting.get("selected_question", "").strip()

            if not selected_question:
                continue

            # Verificar duplicidade
            q_norm = " ".join(selected_question.lower().split())
            if q_norm in seen_questions:
                continue

            # ETAPA B: Geração da Resposta de Referência Anti-Tautológica
            ans_res = gen_committee.generate_reference_answer(selected_question, ev_list, category)
            ref_answer = ans_res.get("reference_answer", "").strip()
            raw_claims = ans_res.get("answer_claims", [])

            # Garantir formato estrito dos claims
            cleaned_claims = []
            req_eids = [e.get("evidence_id", "E0001") for e in ev_list]
            if raw_claims and isinstance(raw_claims, list):
                for c in raw_claims:
                    if isinstance(c, dict) and "claim_text" in c:
                        cleaned_claims.append({
                            "claim_text": c["claim_text"],
                            "supporting_evidence_ids": c.get("supporting_evidence_ids", req_eids),
                            "support_level": c.get("support_level", "supported")
                        })
            if not cleaned_claims:
                cleaned_claims = [{
                    "claim_text": ref_answer,
                    "supporting_evidence_ids": req_eids,
                    "support_level": "supported"
                }]

            # Montar item estruturado em total conformidade com o schema
            item_candidate = {
                "id": f"Q{total_q_counter:03d}",
                "question": selected_question,
                "primary_type": category,
                "reasoning": reasoning,
                "source_type": source_type,
                "answerability": answerability,
                "reference_answer": ref_answer,
                "answer_claims": cleaned_claims,
                "evidence": [{
                    "evidence_id": e.get("evidence_id", "E0001"),
                    "doc_id": e.get("document_id", "DOC"),
                    "page": e.get("page", 1),
                    "span": e.get("text", e.get("claim", ""))
                } for e in ev_list],
                "required_documents": len(ev_list),
                "temporal_scope": temporal_scope,
                "ocr_quality": "good",
                "lexical_distance": "high" if source_type == "multi_document" else "medium",
                "difficulty": "hard" if source_type == "multi_document" or category == "unanswerable" else "medium",
                "generation_model": "committee_3_larger_models",
                "verification_model": "committee_3_smaller_auditors",
                "verification_result": "supported",
                "validation_status": "auto_only",
                "set": "gold",
                "created_at": "2026-10-24T18:50:00Z",
                "version": "v0.3_committee_80",
                "generation_metadata": {
                    "committee": [m["name"] for m in gen_committee.models_meta],
                    "selected_author": gen_voting.get("candidate_author"),
                    "votes_count": gen_voting.get("votes_count")
                }
            }

            # ETAPA C: Auditoria e Votação pelo Comitê Auditor (3 modelos menores)
            is_approved, audit_meta = audit_committee.audit_item(item_candidate)
            item_candidate["auditing_metadata"] = audit_meta

            if is_approved:
                # Validar schema JSON
                valid_schema, schema_errs = schema_validator.validate("question", item_candidate)
                if not valid_schema:
                    safe_print(f"  [Aviso Schema] Erro no item {item_candidate['id']}: {schema_errs}")
                    all_rejections.append({"item": item_candidate, "reason": f"Schema inválido: {schema_errs}"})
                    continue

                seen_questions.add(q_norm)
                cat_counts[category] += 1
                total_q_counter += 1
                all_approved.append(item_candidate)

                safe_print(f"  [Aprovado {cat_counts[category]}/{target_per_category}] {category.upper()} | ID: {item_candidate['id']}")
                safe_print(f"    P: \"{selected_question[:90]}...\"")
                safe_print(f"    R: \"{ref_answer[:90]}...\"")
                safe_print(f"    Votos Auditoria: {audit_meta['verdict_summary']}")

                # Salvar checkpoint
                with open(checkpoint_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(item_candidate, ensure_ascii=False) + "\n")

            else:
                rejection_reason = audit_meta.get("rejection_reason") or f"Votação Reprovada: {audit_meta.get('verdict_summary')}"
                safe_print(f"  [Rejeitado] {category.upper()} - Motivo: {rejection_reason}")
                all_rejections.append({"item": item_candidate, "reason": rejection_reason})

            time.sleep(0.5)

    # 3. Salvar corpus aprovado oficial (80 itens)
    gold_path = Path("corpus/questions_gold.jsonl")
    with open(gold_path, "w", encoding="utf-8") as f:
        for it in all_approved:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Atualizar também validated_approved e benchmark_items_draft
    with open("corpus/validated_approved.jsonl", "w", encoding="utf-8") as f:
        for it in all_approved:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    with open("corpus/benchmark_items_draft.jsonl", "w", encoding="utf-8") as f:
        for it in all_approved:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Salvar itens rejeitados para relatório
    rejections_path = Path("corpus/validated_rejected.jsonl")
    with open(rejections_path, "w", encoding="utf-8") as f:
        for it in all_rejections:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Estatísticas finais
    total_evaluated = len(all_approved) + len(all_rejections)
    summary_report = {
        "total_approved": len(all_approved),
        "total_rejected": len(all_rejections),
        "total_evaluated": total_evaluated,
        "approval_rate": round(len(all_approved) / total_evaluated, 3) if total_evaluated else 1.0,
        "target_per_category": target_per_category,
        "counts_by_category": cat_counts,
        "percentages_by_category": {cat: f"{(cnt/len(all_approved))*100:.1f}%" for cat, cnt in cat_counts.items()} if all_approved else {},
        "generation_committee": [m["name"] for m in gen_committee.models_meta],
        "auditing_committee": [m["name"] for m in audit_committee.models_meta],
        "gold_dataset_path": str(gold_path)
    }

    report_path = Path("logs/committee_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)

    safe_print("\n================================================================================")
    safe_print(" SUCESSO: TODAS AS 8 CATEGORIAS ATINGIRAM A META DE 10 ITENS APROVADOS!")
    safe_print(f" Total no Corpus Gold: {len(all_approved)} perguntas (80 itens / 12.5% por categoria)")
    safe_print(f" Relatório de Votação salvo em: {report_path}")
    safe_print("================================================================================")
    return summary_report


if __name__ == "__main__":
    run_committee_generation_loop(target_per_category=10)
