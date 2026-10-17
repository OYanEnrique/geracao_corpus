import json
import csv
from pathlib import Path


def export_for_human_review():
    print("=== [Etapa 7] Exportação para Validação Humana por Especialistas ===")

    input_file = Path("corpus/validated_approved.jsonl")
    export_csv = Path("corpus/revisao_especialistas_piloto.csv")
    export_md = Path("corpus/revisao_especialistas_piloto.md")

    items = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    # Exportar CSV para preenchimento pelos historiadores
    csv_fields = [
        "id", "question", "primary_type", "source_type", "answerability",
        "reference_answer", "required_docs", "evidence_summary",
        "aprovado_sim_nao", "ajuste_necessario", "observacoes_historiador"
    ]

    with open(export_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()

        for it in items:
            ev_summary = " | ".join([f"[{ev['doc_id']}] {ev['span'][:80]}..." for ev in it.get("evidence", [])])
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
        f.write("# Protocolo de Revisão Humana por Especialistas — Piloto 1\n\n")
        f.write("> **Checklist do Historiador:**\n")
        f.write("> - [ ] A pergunta é plausível para uma pesquisa histórica real?\n")
        f.write("> - [ ] A resposta está integralmente sustentada pelas fontes?\n")
        f.write("> - [ ] Se marcada como 'unanswerable', a informação realmente não consta no acervo?\n")
        f.write("> - [ ] As citações apontam para os trechos corretos?\n\n---\n\n")

        for it in items:
            f.write(f"### Item {it['id']} — {it['primary_type'].upper()} ({it['source_type']})\n\n")
            f.write(f"- **Pergunta:** {it['question']}\n")
            f.write(f"- **Respondibilidade:** `{it['answerability']}`\n")
            f.write(f"- **Resposta de Referência:** {it['reference_answer']}\n")
            f.write(f"- **Evidências:**\n")
            if it.get("evidence"):
                for ev in it["evidence"]:
                    f.write(f"  - Documento: `{ev['doc_id']}` | Trecho: *\"{ev['span']}\"*\n")
            else:
                f.write("  - *(Nenhuma evidência documental — caso de abstenção / adversarial)*\n")
            f.write(f"- **Status:** [ ] Aprovado para Gold  [ ] Manter em Silver  [ ] Rejeitar\n")
            f.write(f"- **Parecer do Revisor:** _________________________________________\n\n---\n\n")

    print(f"[OK] Arquivos de revisao exportados:")
    print(f"  - Planilha CSV: {export_csv}")
    print(f"  - Guia Markdown: {export_md}")


if __name__ == "__main__":
    export_for_human_review()
