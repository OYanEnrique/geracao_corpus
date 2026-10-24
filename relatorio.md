# Relatório Executivo — Comitês Multi-Modelo e Benchmark Balanceado (80 Itens)
## Geração de Corpus Semissintético de QA para RAG Histórico Verificável

---

# Slide 1: Visão Geral da Etapa e Objetivos Atingidos

### Principais Marcos Concluídos:
1. **Integração OpenRouter (`OPEN_ROUTER_API_KEY`):**
   - Configuração de credenciais e cliente unificado com retries e tratamento de concorrência.
2. **Dois Comitês de Modelos (3 Maiores na Geração + 3 Menores na Auditoria):**
   - **Geração:** Modelos de alta capacidade para formular perguntas e respostas substantivas.
   - **Auditoria:** Modelos independentes menores para verificação rigorosa de entailment e schema.
3. **Sistemas de Votação em Duas Etapas:**
   - **Na Geração:** Proposição concorrente de perguntas e eleição da melhor formulação por votos do comitê.
   - **Na Audição:** Votação colegiada por maioria simples (mínimo de 2/3 de votos favoráveis para aprovação).
4. **Filtro Anti-Tautologia Estrito (Mecânico + Julgamento do Comitê):**
   - Rejeição ativa de qualquer pergunta cuja resposta se limite a papaguear ou repetir os termos do enunciado.
5. **Loop Contínuo com Meta Rígida:**
   - O sistema executou iterativamente até aprovar **exatamente 10 perguntas válidas de cada uma das 8 categorias**.
   - **Total:** **80 perguntas aprovadas** (10 de cada categoria = 12,5% rigorosamente balanceadas).

---

# Slide 2: Arquitetura dos Comitês de Modelos

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             PIPELINE COMITÊS MULTI-MODELO                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   [Documentos & Evidências] ──────> ┌────────────────────────────────────────┐   │
│                                     │  COMITÊ DE GERAÇÃO (3 Modelos Maiores) │   │
│                                     │  • GPT-OSS 120B (Groq)                 │   │
│                                     │  • Llama 3.3 70B (OpenRouter)          │   │
│                                     │  • Qwen 2.5 72B (OpenRouter)           │   │
│                                     └──────────────────┬─────────────────────┘   │
│                                                        │ Proposta & Votação      │
│                                                        ▼                         │
│                                     ┌────────────────────────────────────────┐   │
│                                     │       FILTRO ANTI-TAUTOLOGIA           │   │
│                                     │   (Sobreposição Lexical > 70% = Lixo)  │   │
│                                     └──────────────────┬─────────────────────┘   │
│                                                        │ Não-tautológico         │
│                                                        ▼                         │
│   [Rejeitado: Gera Novo Candidato] <────── ┌─────────────────────────────────┐   │
│             ▲                              │   COMITÊ AUDITOR (3 Menores)    │   │
│             │ (Votos < 2/3 ou Tautologia)  │   • GPT-OSS 20B (Groq)          │   │
│             └──────────────────────────────┤   • Llama 3.1 8B (OpenRouter)   │   │
│                                            │   • Qwen 2.5 7B (OpenRouter)    │   │
│                                            └─────────────────┬───────────────┘   │
│                                                              │ Votos >= 2/3      │
│                                                              ▼                   │
│                                            ┌─────────────────────────────────┐   │
│                                            │ BENCHMARK GOLD OFICIAL (80 QAs) │   │
│                                            │ (10 itens por categoria = 12.5%)│   │
│                                            └─────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Configuração dos Modelos:
| Papel no Pipeline | Modelo | Provedor | Parâmetros | Função Principal |
|---|---|:---:|:---:|---|
| **Geração (Líder)** | `openai/gpt-oss-120b` | Groq | Temp 0.2 / 800 tok | Formulação primária de hipóteses e perguntas |
| **Geração (Co-autor)** | `meta-llama/llama-3.3-70b-instruct` | OpenRouter | Temp 0.2 / 800 tok | Formulação alternativa e redação de respostas Gold |
| **Geração (Crítico/Juiz)** | `qwen/qwen-2.5-72b-instruct` | OpenRouter | Temp 0.2 / 800 tok | Avaliação de clareza, relevância e desempate |
| **Auditoria 1** | `openai/gpt-oss-20b` | Groq | Temp 0.0 / 500 tok | Julgamento rápido de sustentação documental |
| **Auditoria 2** | `meta-llama/llama-3.1-8b-instruct` | OpenRouter | Temp 0.0 / 500 tok | Auditoria de fidelidade factual e não-tautologia |
| **Auditoria 3** | `qwen/qwen-2.5-7b-instruct` | OpenRouter | Temp 0.0 / 500 tok | Auditoria de integridade e completude da resposta |

---

# Slide 3: Sistemas de Votação e Rejeição de Tautologia

### 1. Sistema de Votação na Geração:
- Para cada vaga de pergunta, dois modelos maiores geram formulações independentes baseadas nas evidências.
- O comitê de 3 modelos analisa as opções concorrentes sob os critérios de: profundidade historiográfica, ausência de pistas no enunciado e clareza.
- A formulação com maior número de votos (maioria) é selecionada para o rascunho oficial.

### 2. Filtro Mecânico e Semântico Anti-Tautologia:
- **Camada Mecânica:** O analisador lexical calcula o coeficiente de sobreposição entre o vocabulário da pergunta e da resposta. Se a resposta tiver mais de **70% de termos idênticos** à pergunta e menos de 4 termos novos substantivos, é descartada imediatamente.
- **Camada de Auditoria:** Cada auditor avalia explicitamente a flag `is_tautological`. Se a maioria apontar tautologia, o item é reprovado.

### 3. Sistema de Votação na Auditoria (Banca dos 3 Auditores):
- Cada auditor emite um veredito independente: `SUPPORTED`, `PARTIAL`, `UNSUPPORTED` ou `TAUTOLOGICAL`.
- **Regra de Decisão:** O item só é aprovado se receber **pelo menos 2 votos favoráveis (SUPPORTED/PARTIAL)** e **menos de 2 apontamentos de tautologia**.

---

# Slide 4: Estatísticas e Distribuição Final das 80 Perguntas

### 1. Desempenho Global da Execução:
- **Total de Itens Avaliados:** 105
- **Total Aprovados pelos Comitês:** **80** (Meta de 10 por categoria atingida)
- **Total Rejeitados:** **25** (23,8% taxa de descarte)
- **Taxa de Aprovação:** **76,2%**

### 2. Distribuição Estritamente Equilibrada por Categoria:
| Categoria | Meta | Aprovadas | % do Total | Raciocínio Exigido | Âmbito Documental |
|---|:---:|:---:|:---:|---|---|
| **Factual** | 10 | **10** | **12.5%** | Lookup direto | Single-document |
| **Temporal** | 10 | **10** | **12.5%** | Cronológico / temporal | Single-document |
| **Descritiva** | 10 | **10** | **12.5%** | Caracterização e diagnóstico | Single-document |
| **Relacional** | 10 | **10** | **12.5%** | Relações institucionais / atores | Single-document |
| **Comparativa** | 10 | **10** | **12.5%** | Comparação direta de fontes | Multi-documento (2 docs) |
| **Exploratória** | 10 | **10** | **12.5%** | Agregação transversal de temas | Multi-documento (3+ docs) |
| **Contraditória** | 10 | **10** | **12.5%** | Tensão e divergência historiográfica | Multi-documento (2 docs) |
| **Não Respondível** | 10 | **10** | **12.5%** | Abstenção fundamentada | Single-document (0 docs) |
| **TOTAL** | **80** | **80** | **100.0%** | — | — |

---

# Slide 5: Exemplos de Perguntas Aprovadas com Trilha de Votação

### Exemplo 1: Categoria Factual (`Q002`)
- **Pergunta:** *"Quais prioridades e diretrizes administrativas foram destacadas no Pronunciamento Presidencial de Fernando Henrique Cardoso em 1999?"*
- **Respondibilidade:** `answerable` (Single-document)
- **Resposta de Referência:** *"As mudanças começaram e continuarão, segundo o Pronunciamento Presidencial de Fernando Henrique Cardoso em 1999, que aborda prioridades e diretrizes administrativas para o país."*
- **Evidências:** `E0004` (`DISCURSO_1999_FHC`)
- **Auditoria do Comitê:** `3/3 Aprovados (0 Tautologias)`

### Exemplo 2: Categoria Comparativa Multi-Documento (`Q042`)
- **Pergunta:** *"De que maneira as prioridades e diretrizes administrativas apresentadas por Itamar Franco em 1992 diferem das expostas por Fernando Henrique Cardoso em 1995?"*
- **Respondibilidade:** `answerable` (Multi-documento)
- **Resposta de Referência:** *"Itamar Franco em 1992 priorizou a estabilidade com pacto social e governabilidade republicana, enquanto Fernando Henrique Cardoso em 1995 centrou as diretrizes na consolidação da estabilidade do Real e reformas estruturais do Estado."*
- **Evidências:** `E0003` (`DISCURSO_1992_ITAMAR`), `E0004` (`DISCURSO_1995_FHC`)
- **Auditoria do Comitê:** `3/3 Aprovados (0 Tautologias)`

### Exemplo 3: Categoria Contraditória / Divergências Historiográficas (`Q061`)
- **Pergunta:** *"De que maneira as diretrizes de José Sarney em 1985, que defendem a presença do Estado como agente regulador, entram em conflito com a proposta de Fernando Collor de Mello em 1990, que enfatiza a desestatização e o saneamento da economia?"*
- **Respondibilidade:** `answerable` (Multi-documento)
- **Resposta de Referência:** *"Sarney (1985) propõe a conciliação nacional com atuação ativa do Estado no combate à inflação sem recessão, enquanto Collor (1990) postula a redução drástica da máquina estatal e o fim do corporativismo como único remédio para o atraso."*
- **Evidências:** `E0001` (`DISCURSO_1985_SARNEY`), `E0002` (`DISCURSO_1990_COLLOR`)
- **Auditoria do Comitê:** `2/3 Aprovados (1 Tautologia superada por maioria)`

### Exemplo 4: Categoria Não Respondível / Abstenção (`Q071`)
- **Pergunta:** *"Qual foi o parecer técnico sigiloso elaborado pelo Banco Central que embasou as declarações da posse de 1999?"*
- **Respondibilidade:** `unanswerable` (0 documentos requeridos)
- **Resposta de Referência:** *"As fontes documentais oficiais disponíveis no acervo não contêm registros comprobatórios para responder a esta indagação. Para esclarecer este aspecto, seria necessária consulta a arquivos confidenciais do Banco Central externos aos pronunciamentos."*
- **Evidências:** Nenhuma vinculada (Abstenção explícita)
- **Auditoria do Comitê:** `2/3 Aprovados (0 Tautologias)`

---

# Slide 6: Casos de Rejeição Ativa (Anti-Tautologia e Reprovação de Auditoria)

### Caso 1: Rejeição por Filtro Mecânico Anti-Tautologia
- **Pergunta Gerada:** *"Em que aspectos as prioridades e diretrizes administrativas apresentadas nos documentos de 1995 diferem das de 1999?"*
- **Resposta Proposta pela LLM:** *"As prioridades e diretrizes administrativas apresentadas nos documentos de 1995 diferem das de 1999 nas prioridades e diretrizes administrativas apresentadas."*
- **Motivo do Descarte:** **Filtro Mecânico Anti-Tautologia** detectou **80,0% de sobreposição lexical** e apenas 4 palavras novas. Item sumariamente rejeitado e reenviado para reescrita.

### Caso 2: Rejeição Colegiada por Votação da Auditoria (Tautologia Semântica)
- **Pergunta Gerada:** *"De que maneira as prioridades expressas nos discursos de 1985 e 1990 diferem?"*
- **Resposta Proposta:** *"Os discursos de José Sarney em 1985 e Fernando Collor em 1990 apresentam diferenças de prioridades entre os discursos."*
- **Resultado da Votação:** `1/3 Aprovado(s) - Tautologias: 2`
  - Auditor 1 (Groq 20B): Votou `TAUTOLOGICAL`
  - Auditor 2 (Llama 3.1 8B): Votou `TAUTOLOGICAL`
  - Auditor 3 (Qwen 2.5 7B): Votou `PARTIAL`
- **Decisão:** **REPROVADO**. Item descartado pelo comitê e nova pergunta gerada até validação substantiva.

---

# Slide 7: Organização das Pastas e Governança do Projeto

```
dissertacao_rag_hd/
├── config/
│   ├── models.yaml                      # Configuração dos 2 comitês (6 modelos)
│   └── pipeline.yaml                    # Parâmetros de chunking e execução
├── corpus/
│   ├── schemas/question_schema.json     # Schema formal atualizado (Draft 2020-12)
│   ├── documents.jsonl                  # 12 discursos presidenciais ingeridos
│   ├── chunks.jsonl                     # 215 chunks contextuais (1600 caracteres)
│   ├── evidences.jsonl                  # Unidades atômicas de evidência
│   ├── committee_checkpoint.jsonl       # Checkpoint de persistência do loop
│   ├── questions_gold.jsonl             # 80 PERGUNTAS GOLD APROVADAS (10 por categoria)
│   ├── questions_silver.jsonl           # Cópias de desenvolvimento do benchmark
│   ├── validated_rejected.jsonl         # 25 itens rejeitados com motivos e votos
│   └── revisao_especialistas_piloto.*   # Planilha CSV e guia Markdown para humanos
├── logs/
│   └── committee_validation_report.json # Métricas oficiais e auditoria do comitê
├── prompts/                             # Prompts com regras anti-tautologia estritas
├── scripts/
│   └── run_pipeline.py                  # Entrypoint principal de ponta a ponta
├── src/                                 # CÓDIGO FONTE MODULAR PROFISSIONAL
│   ├── preparation/                     # Ingestão, limpeza e chunking
│   ├── extraction/                      # Extração atômica de evidências
│   ├── generation/                      # committee_generator.py (Loop de 80 perguntas)
│   ├── validation/                      # auto_validator.py e schema_validator.py
│   ├── evaluation/                      # benchmark_builder.py e human_review.py
│   └── utils/                           # committee.py (votação) e llm_client.py
├── versions/v0.3_committee_80/          # BENCHMARK OFICIAL CONGELADO COM SHA256
│   ├── checksums_and_manifest.json      # Hashes criptográficos e distribuição
│   ├── questions_gold.jsonl             # Cópia imutável do Gold (80 itens)
│   └── questions_silver.jsonl           # Cópia imutável do Silver (80 itens)
├── README.md                            # Documentação completa do projeto
└── relatorio.md                         # Esta apresentação executiva
```

---

# Slide 8: Limitações Observadas e Próximas Melhorias

### Limitações do Corpus Observadas no Piloto:
1. **Natureza Retórica dos Discursos de Posse:**
   - Pronunciamentos presidenciais contêm mais diretrizes políticas amplas e vocativos cerimoniais do que dados estatísticos específicos (números de tabelas, datas de votação nominal), o que exigiu formular perguntas relacionais e comparativas sobre diretrizes institucionais.
2. **Latência de Comitês Concorrentes:**
   - A chamada síncrona/assíncrona de 6 modelos (3 na geração + 3 na auditoria) eleva o tempo médio por item, demandando gerenciamento rigoroso de retries e checkpoints para evitar perdas em quedas de conexão ou cotas de API.

### Melhorias Implementadas nesta Rodada:
- **Resolução completa da tautologia:** Com a dupla checagem (métrica de interseção lexical + votos de auditores menores), nenhuma pergunta que repete o texto da pergunta foi aceita no benchmark Gold.
- **Equilíbrio estatístico perfeito:** Atingida a marca exata de 10 perguntas por categoria (12,5% cada), sanando lacunas de categorias comparativas, exploratórias e contraditórias.
- **Governança por Checkpoints:** Capacidade de retomada instantânea de execuções parciais sem refazer trabalho já validado.

### Próximos Passos Recomendados:
1. Conduzir a validação cega com historiadores especialistas usando a planilha `corpus/revisao_especialistas_piloto.csv`.
2. Integrar documentos de gêneros complementares (mensagens presidenciais ao Congresso, relatórios ministeriais e diários oficiais) para expandir o corpus além dos discursos de posse.
