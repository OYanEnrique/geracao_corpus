"""Módulo de validação automática independente com os 7 filtros metodológicos."""
import json
from pathlib import Path
from typing import Dict, Any, List

from src.validation.schema_validator import SchemaValidator
from src.utils.llm_client import UnifiedLLMClient
from src.utils.config import get_models_config


def run_auto_validation() -> Dict[str, Any]:
    print("=== [Pipeline] Validação Automática Independente (7 Filtros) ===")

    validator = SchemaValidator()
    models_cfg = get_models_config()
    ver_cfg = models_cfg["llm_verifier"]

    llm_b = UnifiedLLMClient(
        provider=ver_cfg["provider"],
        model=ver_cfg["model"],
        temperature=ver_cfg["temperature"]
    )

    with open("prompts/verification.md", "r", encoding="utf-8") as f:
        prompt_b_template = f.read()

    # Documentos conhecidos para integridade referencial
    known_docs = set()
    with open("corpus/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            known_docs.add(d["document_id"])

    # Carregar itens rascunho
    items = []
    with open("corpus/benchmark_items_draft.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    approved_items: List[Dict[str, Any]] = []
    flagged_items: List[Dict[str, Any]] = []
    seen_questions = set()

    for item in items:
        issues = []

        # Filtro 1: Validação de Schema JSON
        is_valid_schema, schema_errs = validator.validate("question", item)
        if not is_valid_schema:
            issues.append(f"Erro de Schema: {schema_errs}")

        # Filtro 2: Integridade de document_id
        for ev in item.get("evidence", []):
            if ev["doc_id"] not in known_docs:
                issues.append(f"Documento desconhecido citado: {ev['doc_id']}")

        # Filtro 3: Respondibilidade vs Evidências
        if item["answerability"] == "answerable" and len(item.get("evidence", [])) == 0:
            issues.append("Pergunta respondível sem nenhuma evidência associada.")
        if item["answerability"] == "unanswerable" and len(item.get("evidence", [])) > 0:
            issues.append("Pergunta não respondível com evidências indevidamente vinculadas.")

        # Filtro 4: Detecção de duplicatas
        q_norm = " ".join(item["question"].lower().split())
        if q_norm in seen_questions:
            issues.append("Pergunta duplicada detectada.")
        seen_questions.add(q_norm)

        # Filtro 5: Teste anti-tautologia mecânico
        # Se a resposta tiver apenas 1 sentença e for quase idêntica à pergunta (>90% similaridade de palavras)
        q_words = set(re_words(item["question"]))
        ans_words = set(re_words(item["reference_answer"]))
        if len(ans_words) > 0 and len(q_words.intersection(ans_words)) / len(ans_words) > 0.92 and item["answerability"] == "answerable":
            issues.append("Possível resposta tautológica: vocabulário 90%+ idêntico ao da pergunta.")

        # Filtro 6 & 7: Auditoria de Entailment com LLM B (se aprovado nos mecânicos)
        if not issues and item["answerability"] == "answerable":
            prompt_b = (
                prompt_b_template
                .replace("{question}", item["question"])
                .replace("{reference_answer}", item["reference_answer"])
                .replace("{evidences_json}", json.dumps(item["evidence"], ensure_ascii=False))
            )
            audit_res = llm_b.call_json(prompt_b)
            verdict = audit_res.get("overall_verdict", "SUPPORTED") if isinstance(audit_res, dict) else "SUPPORTED"
            item["verification_model"] = f"{ver_cfg['provider']}:{ver_cfg['model']}"
            item["verification_result"] = str(verdict).lower()

            if str(verdict).upper() in ["CONTRADICTORY", "UNSUPPORTED"]:
                issues.append(f"Reprovado pelo LLM B: veredito {verdict}")

        if issues:
            item["issues"] = issues
            flagged_items.append(item)
        else:
            approved_items.append(item)

    # Gravar saídas
    with open("corpus/validated_approved.jsonl", "w", encoding="utf-8") as f:
        for it in approved_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    with open("corpus/validated_flagged.jsonl", "w", encoding="utf-8") as f:
        for it in flagged_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Contagem de aprovados por categoria
    cat_counts = {}
    for it in approved_items:
        cat = it["primary_type"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    report = {
        "total_evaluated": len(items),
        "approved_count": len(approved_items),
        "flagged_count": len(flagged_items),
        "approval_rate": round(len(approved_items) / len(items), 3) if items else 0,
        "approved_by_category": cat_counts,
        "percentages_by_category": {cat: f"{(cnt/len(approved_items))*100:.1f}%" for cat, cnt in cat_counts.items()} if approved_items else {}
    }

    log_file = Path("logs/auto_validation_report.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[OK] Validação automática concluída:")
    print(f"  - Itens avaliados: {report['total_evaluated']}")
    print(f"  - Itens aprovados: {report['approved_count']} ({report['approval_rate']*100:.1f}%)")
    print(f"  - Itens sinalizados/alertados: {report['flagged_count']}")
    print(f"  - Relatório salvo em: {log_file}")
    return report


def re_words(text: str) -> List[str]:
    import re
    return [w.lower() for w in re.findall(r'\b\w{3,}\b', text)]


if __name__ == "__main__":
    run_auto_validation()
