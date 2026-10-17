# Apresentação do Projeto & Execução do Piloto 1
## Construção de Corpus Semissintético de QA para RAG Verificável em Acervos Históricos

---

# Slide 1: Visão Geral e Proposta do Projeto

### O Problema Central
* **RAG Convencional Falha em Acervos Históricos:**
  * Alucinação em datas, nomes e causalidades.
  * Citações genéricas que não comprovam o que o sistema afirmou.
  * Incapacidade de declarar ignorância diante de lacunas documentais.

### A Solução Metodológica
* **RAG Verificável com Benchmark Semissintético:**
  * Citação estrita por afirmação (*claim-level grounding*).
  * Mecanismo formal de **abstenção** (*unanswerable questions*).
  * Princípio pétreo: **a evidência documental precede a pergunta**; o modelo não inventa fatos.

---

# Slide 2: Arquitetura do Pipeline Metodológico

```
[1. Ingestão & Metadados] ──> [2. Limpeza & Segmentação] ──> [3. Extração de Evidências]
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
[4. Geração de Perguntas] ──> [5. Resposta de Referência] ──> [6. Validação Cruzada A/B]
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
[7. Revisão Especialista] ──> [8. Separação Gold/Silver & Congelamento SHA256]
```

* **Separação de Papéis:** Modelo Gerador (LLM A) formula; Modelo Auditor (LLM B) valida de forma independente para evitar auto-aprovação enviesada.

---

# Slide 3: Modelos e Tecnologias Empregados

### Modelos de Linguagem (LLMs)
* **LLM A (Gerador Principal):** `openai/gpt-oss-120b` (via provedor Groq)
  * Responsável pela extração atômica de evidências, formulação de perguntas e elaboração das respostas de referência.
* **LLM B (Auditor Independente):** `openai/gpt-oss-20b` (via provedor Groq)
  * Responsável por auditar o *entailment* (sustentação textual estrita) e flagrar extrapolações interpretativas.

### Engenharia e Padrões
* **Linguagem & Validação:** Python 3.12 + Schemas estritos **JSON Schema Draft 2020-12**.
* **Integridade Criptográfica:** Hash **SHA256** para auditoria e congelamento de versão (*data versioning*).

---

# Slide 4: O Corpus do Piloto 1 — Discursos Presidenciais

### Recorte Utilizado
* **12 discursos de posse/pronunciamentos oficiais (1985 a 2023):**
  * Sarney (1985), Collor (1990), Itamar (1992), FHC (1995/1999), Lula (2003/2007/2023), Dilma (2011/2015), Temer (2016) e Bolsonaro (2019).
* **Metadados Estruturados:** Registrados na pasta `data/raw/piloto_1/` no arquivo `metadados_discursos.csv` com proveniência em `proveniencia_base_publica.json`.

### Por que esse corpus?
* Garante **risco zero de vazamento de dados** (*data leakage*) para a dissertação final (que usará o acervo histórico do RIMA-UFRRJ).
* Testa a densidade de fatos, datas, compromissos de governo e comparações temporais.

---

# Slide 5: Organização dos Diretórios do Projeto

```
dissertacao_rag_hd/
├── config/
│   ├── pipeline.yaml                  # Parâmetros operacionais do pipeline
│   └── models.yaml                    # Configuração de provedores e modelos (Groq)
├── corpus/
│   ├── schemas/                       # Schemas JSON formais (document, evidence, question)
│   ├── documents.jsonl                # Catálogo estruturado dos 12 documentos
│   ├── chunks.jsonl                   # 215 trechos segmentados com controle de caracteres
│   ├── evidences.jsonl                # 109 evidências atômicas validadas
│   ├── questions_gold.jsonl           # Benchmark oficial Gold auditado
│   ├── questions_silver.jsonl         # Conjunto Silver para desenvolvimento
│   └── revisao_especialistas_piloto.* # Protocolo em .md e .csv para historiadores
├── data/raw/piloto_1/                 # Arquivos brutos e metadados de entrada
├── logs/auto_validation_report.json   # Relatório de aprovação/rejeição dos 7 filtros
├── prompts/                           # 4 templates versionados de prompts (extração, Q, A, auditoria)
├── scripts/                           # Pipeline executável (01_prepare a 07_build_gold_silver)
│   └── utils/                         # Chunker de sentenças, limpador, validador de schema e LLM client
└── versions/v0.1_pilot1/              # Versão congelada com manifesto e checksum SHA256
```

---

# Slide 6: Exemplo 1 — Pergunta Factual com Limitação Declarada

### Item Q002 (Single-Document)
* **Pergunta:** *“Qual era o montante da dívida externa que José Sarney herdou ao assumir a presidência em 1985, e como esse valor se comparava com as dívidas externas de outros países na mesma época?”*
* **Respondibilidade:** `answerable` (Respondível)
* **Dificuldade / Raciocínio:** `medium` / `lookup`
* **Resposta de Referência (Gold):**
  > *“Os documentos indicam que José Sarney herdou, ao assumir a presidência em 1985, a maior dívida externa do mundo, mas não fornecem o valor numérico exato. Assim, sabe‑se que a dívida que ele recebeu era superior às dívidas externas de quaisquer outros países na mesma época, embora o montante específico não esteja mencionado nos textos disponíveis.”*
* **Evidência Documental Ancorada:**
  * **Documento:** `DISCURSO_1985_SARNEY` (Página 1 / Chunk 2)
  * **Trecho literal (*span*):** *“a maior dívida externa do mundo;”*

---

# Slide 7: Exemplo 2 — Pergunta Descritiva de Diagnóstico

### Item Q005 (Single-Document)
* **Pergunta:** *“Quais problemas socioeconômicos Itamar Franco destacou como presentes no Brasil em seu pronunciamento de 1992?”*
* **Respondibilidade:** `answerable` (Respondível)
* **Dificuldade / Raciocínio:** `medium` / `lookup`
* **Resposta de Referência (Gold):**
  > *“Em seu pronunciamento de 1992, Itamar Franco destacou que o Brasil convivia com a fome, a miséria e o desemprego de milhões de compatriotas.”*
* **Evidência Documental Ancorada:**
  * **Documento:** `DISCURSO_1992_ITAMAR` (Página 1 / Chunk 2)
  * **Trecho literal (*span*):** *“a fome, a miséria e o desemprego de milhões de compatriotas”*

---

# Slide 8: Exemplo 3 — Pergunta Comparativa Multi-Documento

### Item Q025 (Multi-Document — 1985 vs. 1990)
* **Pergunta:** *“Como as declarações iniciais de posse de José Sarney em 1985 e Fernando Collor de Mello em 1990 caracterizam as circunstâncias e os desafios ao assumirem a presidência?”*
* **Respondibilidade:** `answerable` (Respondível)
* **Dificuldade / Raciocínio:** `hard` / `comparison` (Requer 2 documentos)
* **Resposta de Referência (Gold):**
  > *“Em 1985, José Sarney declarou que herdou a tarefa de administrar a maior crise política da história brasileira. Em 1990, Fernando Collor de Mello caracterizou a presidência como o mandato mais honroso e o desafio mais difícil a que um homem público pode aspirar.”*
* **Evidências Documentais Ancoradas:**
  1. `DISCURSO_1985_SARNEY`: *“Herdei para administrar a maior crise política da história brasileira;”*
  2. `DISCURSO_1990_COLLOR`: *“para receber o mandato mais honroso e o desafio mais difícil a que um homem público pode aspirar”*

---

# Slide 9: Exemplo 4 — Pergunta Adversarial & Abstenção

### Item Q031 (Informação Ausente / Temporal Hard Negative)
* **Pergunta:** *“Qual foi a taxa exata de desemprego apurada pelo IBGE no terceiro trimestre de 1987 segundo o discurso de posse de 1985?”*
* **Respondibilidade:** `unanswerable` (Não Respondível)
* **Dificuldade / Raciocínio:** `hard` / `temporal` (Anacronismo deliberado)
* **Resposta de Referência (Gold):**
  > *“Os documentos recuperados no acervo não contêm informações suficientes para responder à pergunta sobre 1987. Para esclarecer este ponto, seria necessário localizar registros oficiais externos específicos não documentados nos discursos de posse.”*
* **Evidência Documental:**
  * `[]` *(Nenhuma evidência vinculada — o sistema deve recusar responder categoricamente).*

---

# Slide 10: Auditoria Automática e Tipos da Proposta

### Desempenho dos 7 Filtros Automáticos (Etapa 6)
* **Total avaliado:** 34 itens | **Aprovados:** 30 (88.2%) | **Sinalizados/Rejeitados:** 4 (11.8%)
* **Relatório:** Salvo na pasta `logs/` no arquivo `auto_validation_report.json`.

### O que aconteceu com as categorias da proposta?
| Categoria na Proposta | Presente no Piloto? | Observação |
|---|:---:|---|
| **Factual / Entidade** | Sim | Cobertura alta (dados econômicos, nomes, instituições). |
| **Descritiva** | Sim | Cobertura alta (diagnósticos de crise, problemas sociais). |
| **Comparativa (Multi-doc)** | Sim | 26.7% do conjunto Gold (cumpre a meta de 30–40%). |
| **Não Respondível / Abstenção** | Sim | 13.3% do conjunto Gold (cumpre a meta de 10–15%). |
| **Contraditória** | Parcial / Ausente | **Motivo:** Discursos de posse são declarações públicas unilaterais individuais, sem confronto direto de dados no mesmo evento; contradições documentais plenas serão capturadas no RIMA (ex.: divergências entre atas e relatórios de obras). |
| **Exploratória** | Ausente | Perguntas do tipo "quais fontes tratam de X" foram postergadas para quando houver o índice vetorial/BM25 completo montado. |

---

# Slide 11: O Filtro Independente em Ação (LLM B)

### Como o LLM B evitou "alucinações elegantes"
O auditor (`openai/gpt-oss-20b`) rejeitou itens em que a resposta tentou "adivinhar" ou "filosofar" além da fonte:

```
Item Q003:
- Evidência literal: "Orgulho-me de ter pertencido à Câmara dos Deputados"
- Resposta do LLM A: "Ele ocupava o cargo de deputado federal..."
- Veredito do LLM B: REPROVADO (UNSUPPORTED)
  Justificativa: O texto diz apenas ter pertencido à Casa, sem explicitar a nomenclatura do cargo no trecho.

Item Q029:
- Resposta do LLM A adicionou: "...os discursos se contrapõem pois um apela ao coletivo e outro à religiosidade..."
- Veredito do LLM B: REPROVADO (UNSUPPORTED)
  Justificativa: Análise interpretativa e sociológica não declarada textualmente pelos presidentes.
```

* **Resultado:** Itens com extrapolações foram movidos para a pasta `corpus/` no arquivo `validated_flagged.jsonl`, protegendo o conjunto Gold.

---

# Slide 12: Limitações Observadas no Piloto

### 1. Efeito de Resposta Espelhada / Tautológica (*Self-repeating QA*)
* **O Fenômeno:** Algumas perguntas geradas trazem quase toda a resposta em seu próprio enunciado.
  * *Exemplo (Item Q004):* Pergunta: *"Qual foi a atuação destacada de Lindolfo Collor na Câmara...?"* ➔ Resposta: *"Lindolfo Collor teve atuação destacada na Câmara..."*
* **Causa Identificada:** Quando a evidência é muito curta e estrita, o gerador de perguntas usa as próprias palavras da *claim* para formular a dúvida.
* **Impacto no RAG:** Avalia apenas se o buscador acha a frase exata (*lexical lookup* trivial), sem exigir raciocínio real de agregação.

### 2. Limitações Próprias do Corpus de Discursos
* **Sem Paginação Real:** Documentos em texto contínuo (`char_start`/`char_end`), sem páginas físicas escaneadas.
* **Ausência de Ruído de OCR:** Transcrições digitais limpas não estressam o módulo de correção de caracteres degradados.

---

# Slide 13: Próximos Passos e Melhorias para o RIMA

### Melhorias Técnicas Imediatas
1. **Injeção de Paráfrases e Distância Lexical:**
   * Obrigar o prompt de perguntas a usar sinônimos e formulações indiretas para eliminar as respostas espelhadas/tautológicas.
2. **Chunking Semântico Expandido:**
   * Em vez de fornecer apenas 1 sentença para o gerador de perguntas, fornecer o parágrafo contextual amplo para que a pergunta nasça de um problema e a resposta capture múltiplos dados.

### Transição para o Corpus do RIMA-UFRRJ
1. Inserir os PDFs/imagens escaneadas do RIMA na pasta `data/raw/`.
2. Executar o pipeline validado (`scripts/01_prepare_documents.py` a `07_build_gold_silver.py`).
3. Conduzir a revisão por pares com historiadores utilizando a planilha na pasta `corpus/` (`revisao_especialistas_piloto.csv`).

---

# Slide 14: Conclusão e Entrega

* **O pipeline demonstrou viabilidade científica e operacional completa.**
* Toda a esteira de código, validações de schemas e dupla checagem por IA estão testadas, documentadas e versionadas.
* **Artefatos Disponíveis:**
  * Plano Metodológico Geral: pasta `contexto/plano_implementacao_corpus_qa.md`
  * Conjunto Gold Congelado: pasta `versions/v0.1_pilot1/questions_gold.jsonl`
  * Guia de Revisão Humana: pasta `corpus/revisao_especialistas_piloto.md`
  * Relatório em Slides: raiz do projeto `relatorio.md`
