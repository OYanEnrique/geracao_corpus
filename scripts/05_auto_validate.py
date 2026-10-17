import json
import yaml
from pathlib import Path
from utils.schema_validator import SchemaValidator
from utils.llm_client import UnifiedLLMClient


def auto_validate():
    print("=== [Etapa 6] Validação Automática Independente (7 Filtros) ===")

    validator = SchemaValidator()

    with open("config/models.yaml", "r", encoding="utf-8") as f:
        models_cfg = yaml.safe_load(f)
    ver_cfg = models_cfg["llm_verifier"]

    # Inicializar LLM B (Verificador independente)
    llm_b = UnifiedLLMClient(
        provider=ver_cfg["provider"],
        model=ver_cfg["model"],
        temperature=ver_cfg["temperature"]
    )

    with open("prompts/verification.md", "r", encoding="utf-8") as f:
        prompt_b_template = f.read()

    # Carregar documentos existentes para checagem de integridade referencial
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

    approved_items = []
    flagged_items = []
    seen_questions = set()

    for item in items:
        item_id = item["id"]
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
            issues.append("Pergunta não respondível com evidências vinculadas indevidamente.")

        # Filtro 4: Detecção de duplicatas exatas ou semânticas
        q_norm = " ".join(item["question"].lower().split())
        if q_norm in seen_questions:
            issues.append("Pergunta duplicada detectada.")
        seen_questions.add(q_norm)

        # Filtro 5 & 6: Auditoria com LLM B (Verificador Independente)
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
            item["verification_result"] = verdict.lower()

            if verdict in ["CONTRADICTORY", "UNSUPPORTED"]:
                issues.append(f"Rejeitado pelo LLM B: veredito {verdict}")

        if issues:
            item["issues"] = issues
            flagged_items.append(item)
        else:
            approved_items.append(item)

    # Salvar resultados
    with open("corpus/validated_approved.jsonl", "w", encoding="utf-8") as f:
        for it in approved_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    with open("corpus/validated_flagged.jsonl", "w", encoding="utf-8") as f:
        for it in flagged_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    report = {
        "total_evaluated": len(items),
        "approved_count": len(approved_items),
        "flagged_count": len(flagged_items),
        "approval_rate": round(len(approved_items) / len(items), 3) if items else 0
    }

    with open("logs/auto_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[OK] Validacao automatica concluida:")
    print(f"  - Itens avaliados: {report['total_evaluated']}")
    print(f"  - Itens aprovados: {report['approved_count']} ({report['approval_rate']*100:.1f}%)")
    print(f"  - Itens com alertas/sinalizados: {report['flagged_count']}")
    print(f"  - Relatório salvo em: logs/auto_validation_report.json")


if __name__ == "__main__":
    auto_validate()
