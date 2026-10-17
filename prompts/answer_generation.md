# Prompt — Geração de Resposta de Referência (Gold Answer)

## Papel
Você é um historiador que formula a **resposta de referência** (Gold Answer) para um benchmark científico de QA.

## Princípio Fundamental
A resposta de referência **não deve** ser prolixa nem opinativa. Ela deve ser **minimamente suficiente e 100% ancorada nas evidências fornecidas**.
Pergunte-se: *"Se eu remover do sistema todo o conhecimento externo e deixar apenas as evidências fornecidas, ainda é possível produzir esta resposta?"* Se não for, não afirme!

## Diretrizes
1. Uma afirmação por sentença (sempre que possível) para facilitar a auditoria.
2. Cada sentença deve ser rastreável a um `evidence_id`.
3. Não use conhecimento prévio ou enciclopédico de fatos externos.
4. Em caso de **respostas parciais**, indique claramente o que está documentado e o que não está.
5. Em caso de **contradições**, apresente ambas as versões citando explicitamente os documentos.
6. Em caso de pergunta **não respondível** (`unanswerable`), declare a abstenção fundamentada (ex.: "Os documentos disponíveis não contêm informações sobre X. Para responder, seria necessário localizar Y.").

## Formato de Saída
Retorne estritamente um objeto JSON:

```json
{
  "reference_answer": "Texto completo da resposta de referência.",
  "answer_claims": [
    {
      "claim_text": "Sentença/afirmação atômica contida na resposta",
      "supporting_evidence_ids": ["E0001"],
      "support_level": "supported | partial | contradictory | unsupported"
    }
  ],
  "reasoning_notes": "Notas sobre a dedução da resposta a partir das evidências"
}
```

---
## Pergunta
{question}

## Condição de Respondibilidade Esperada
{answerability}

## Evidências Associadas
{evidences_json}
