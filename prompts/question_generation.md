# Prompt — Geração de Perguntas de Pesquisa

## Papel
Você é um pesquisador em Humanidades Digitais formulando perguntas de pesquisa histórica para avaliar um sistema RAG verificável.

## Diretrizes
1. As perguntas devem soar naturais para uma investigação histórica real.
2. Cada pergunta deve ser ancorada **estritamente** nas evidências documentais fornecidas (ou ser deliberadamente não respondível / adversarial, quando solicitado).
3. Varie os tipos de perguntas:
   - **factual**: fatos, entidades, cargos, números diretos
   - **temporal**: datas, sequências, períodos
   - **descriptive**: problemas, diagnósticos, diretrizes descritas
   - **relational**: relações entre indivíduos, instituições e cargos
   - **comparative / multi_document**: comparação entre dois documentos/momentos
   - **contradictory**: quando fontes ou trechos divergem
   - **unanswerable**: perguntas sem evidência suficiente nas fontes ou com premissas falsas
4. Inclua variação de linguagem e distância lexical (perguntas com sinônimos e paráfrases da fonte).

## Formato de Saída
Retorne estritamente um array JSON de objetos:

```json
[
  {
    "question": "Texto da pergunta de pesquisa em português",
    "primary_type": "factual | temporal | descriptive | relational | comparative | exploratory | contradictory",
    "reasoning": "lookup | temporal | relation | aggregation | comparison | contradiction",
    "source_type": "single_document | multi_document",
    "answerability": "answerable | partial | unanswerable",
    "required_evidence_ids": ["E0001", "E0002"],
    "required_documents": 1,
    "temporal_scope": "1985-1990",
    "lexical_distance": "low | medium | high",
    "difficulty": "easy | medium | hard"
  }
]
```

---
## Evidências Disponíveis para Construção

{evidences_json}
