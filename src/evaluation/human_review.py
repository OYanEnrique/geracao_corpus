"""Exportador de dados para o protocolo de validação humana por especialistas."""
import json
import csv
from pathlib import Path
from typing import Dict, Any


def run_human_review_export(input_path: str = "corpus/validated_approved.jsonl") -> Dict[str, Any]:
    print("=== [Pipeline] Exportação para Validação Humana por Especialistas ===")

    input_file = Path(input_path)
    export_csv = Path("corpus/revisao_especialistas_piloto.csv")
    export_md = Path("corpus/revisao_especialistas_piloto.md")

    items = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    # Exportar CSV
    csv_fields = [
        "id", "question", "primary_type", "source_type", "answerability",
        "reference_answer", "required_docs", "evidence_summary",
        "aprovado_sim_nao", "ajuste_necessario", "observacoes_historiador"
    ]

    with open(export_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()

        for it in items:
            ev_summary = " | ".join([f"[{ev['doc_id']}] {ev['span'][:90]}..." for ev in it.get("evidence", [])])
            writer.writerow({
                "id": it["id"],
                "question": it["question"],
                "primary_type": it["primary_type"],
                "source_type": it["source_type"],
                "answerability": it["answerability"],
                "reference_answer": it["reference_answer"],
                "required_docs": it["required_documents"],
                "evidence_summary": ev_summary if ev_summary else "(Nenhuma - Pergunta de abstenção)",
                "aprovado_sim_nao": "SIM",
                "ajuste_necessario": "",
                "observacoes_historiador": ""
            })

    # Exportar Markdown estruturado com checklist
    with open(export_md, "w", encoding="utf-8") as f:
        f.write("# Protocolo de Revisão Humana por Especialistas — Benchmark Equilibrado\n\n")
        f.write("> **Checklist do Historiador:**\n")
        f.write("> - [ ] A pergunta é plausível para uma pesquisa histórica real?\n")
        f.write("> - [ ] A resposta está integralmente sustentada pelas fontes indicadas?\n")
        f.write("> - [ ] A resposta acrescenta a informação e NÃO apenas repete os termos da pergunta?\n")
        f.write("> - [ ] Em contradições, ambas as versões divergentes foram registradas de forma imparcial?\n")
        f.write("> - [ ] Se marcada como 'unanswerable', a informação realmente não consta no acervo?\n\n---\n\n")

        for it in items:
            f.write(f"### Item {it['id']} — {it['primary_type'].upper()} ({it['source_type']})\n\n")
            f.write(f"- **Pergunta:** {it['question']}\n")
            f.write(f"- **Tipo Primário:** `{it['primary_type']}` | **Respondibilidade:** `{it['answerability']}`\n")
            f.write(f"- **Resposta de Referência (Gold):** {it['reference_answer']}\n")
            f.write(f"- **Evidências Documentais Vinculadas:**\n")
            if it.get("evidence"):
                for ev in it["evidence"]:
                    f.write(f"  - Documento: `{ev['doc_id']}` | Trecho: *\"{ev['span']}\"*\n")
            else:
                f.write("  - *(Nenhuma evidência documental — caso de abstenção / adversarial)*\n")
            f.write(f"- **Status da Avaliação:** [ ] Aprovado para Gold  [ ] Manter em Silver  [ ] Rejeitar\n")
            f.write(f"- **Parecer do Revisor:** _________________________________________\n\n---\n\n")

    summary = {
        "items_exported": len(items),
        "csv_path": str(export_csv),
        "md_path": str(export_md)
    }
    print(f"[OK] Revisão humana exportada: {len(items)} itens em {export_md} e {export_csv}")
    return summary


if __name__ == "__main__":
    run_human_review_export()
