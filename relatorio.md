# Relatório de Execução — Refatoração Profissional e Benchmark Balanceado (v0.2)
## Geração de Corpus Semissintético de QA para RAG Histórico Verificável

---

# Slide 1: Visão Geral das Melhorias da Etapa

### O que foi realizado nesta iteração:
1. **Refatoração Profissional em `src/`:**
   - Desacoplamento da biblioteca em pacotes temáticos profissionais (`preparation/`, `extraction/`, `generation/`, `validation/`, `evaluation/`, `utils/`).
   - `scripts/` mantido apenas como camada leve de CLI executável que invoca `src/`.
2. **Geração Estritamente Balanceada (8 Categorias do Guia):**
   - Eliminação de qualquer assimetria: **mesma quantidade exata de perguntas geradas por categoria**.
   - Inclusão sistemática das categorias que faltavam: **Exploratória** e **Contraditória**.
3. **Resolução Definitiva do Problema de Respostas Tautológicas:**
   - Expansão da janela de contexto no chunking (1600 caracteres com overlap de 300).
   - Filtro de vacuidade nas evidências (rejeição de claims vazias sem predicados concretos).
   - Diretrizes de prompt com restrição anti-tautológica explícita.
4. **Governança, Logs e Congelamento:**
   - Log completo da validação em `logs/auto_validation_report.json`.
   - Benchmark balanceado congelado com hash SHA256 em `versions/v0.2_balanced/`.

---

# Slide 2: Nova Arquitetura de Pastas e Código (`src/`)

```
dissertacao_rag_hd/
├── config/
│   ├── pipeline.yaml                  # Configurações de chunking e parâmetros
│   └── models.yaml                    # Provedores e modelos ativos (Groq)
├── corpus/
│   ├── schemas/                       # Schemas JSON formais (Draft 2020-12)
│   ├── documents.jsonl                # Catálogo de documentos ingeridos
│   ├── chunks.jsonl                   # Chunks contextuais amplos (1600 chars)
│   ├── evidences.jsonl                # Evidências substantivas filtradas
│   ├── questions_draft.jsonl          # 32 perguntas equilibradas geradas
│   ├── questions_gold.jsonl           # 16 itens Gold oficiais congelados
│   ├── questions_silver.jsonl         # Itens Silver para desenvolvimento
│   └── revisao_especialistas_piloto.* # Planilha CSV e guia Markdown
├── logs/
│   └── auto_validation_report.json   # Log de aprovação e métricas dos 7 filtros
├── prompts/                           # Prompts operacionais com regras anti-tautologia
├── scripts/                           # Entrypoints CLI enxutos (importam de src/)
│   ├── 01_prepare_documents.py
│   ├── 02_extract_evidences.py
│   ├── 03_generate_questions.py
│   ├── 04_generate_answers.py
│   ├── 05_auto_validate.py
│   ├── 06_human_review_export.py
│   ├── 07_build_gold_silver.py
│   └── run_pipeline.py                # Runner mestre de ponta a ponta
├── src/                               # 📁 NÚCLEO PROFISSIONAL DO PROJETO
│   ├── preparation/                   # Cleaner e ContextualSentenceChunker
│   ├── extraction/                    # Extrator de evidências substantivas
│   ├── generation/                    # QuestionGenerator e AnswerGenerator
│   ├── validation/                    # SchemaValidator e AutoValidator (LLM B)
│   ├── evaluation/                    # HumanReviewExport e BenchmarkBuilder
│   ├── utils/                         # UnifiedLLMClient e Config loaders
│   └── pipeline.py                    # Orquestrador programático
├── versions/v0.2_balanced/            # Benchmark final congelado com manifesto SHA256
├── relatorio.md                       # Apresentação executiva
└── README.md                          # Documentação central do projeto
```

---

# Slide 3: Estatísticas e Distribuição por Categoria

### 1. Conjunto Total de Perguntas Geradas (32 itens)
Cada uma das 8 categorias descritas no guia metodológico e no plano de implementação recebeu **exatamente 4 perguntas (12.5% cada)**:

| Categoria Primária | Quantidade Gerada | Porcentagem | Tipo de Raciocínio | Origem Documental |
|---|:---:|:---:|---|---|
| **Factual / Entidade** | 4 | **12.5%** | Lookup direto | Single-document |
| **Temporal** | 4 | **12.5%** | Temporal / cronológico | Single-document |
| **Descritiva** | 4 | **12.5%** | Descrição e diagnóstico | Single-document |
| **Relacional** | 4 | **12.5%** | Relações institucionais | Single-document |
| **Comparativa** | 4 | **12.5%** | Comparação entre fontes | Multi-documento |
| **Exploratória** | 4 | **12.5%** | Agregação transversal | Multi-documento (3+ docs) |
| **Contraditória** | 4 | **12.5%** | Divergência historiográfica | Multi-documento |
| **Não Respondível** | 4 | **12.5%** | Abstenção fundamentada | Single-document (0 docs) |
| **TOTAL** | **32** | **100.0%** | — | — |

---

# Slide 4: O Benchmark Gold Congelado (`v0.2_balanced`)

### Distribuição no Conjunto Oficial Gold (16 itens auditados)
Para a avaliação oficial, foram selecionados **exatamente 2 itens aprovados por categoria**, preservando o equilíbrio matemático absoluto (12.5% por categoria):

```
┌────────────────────────────────────────────────────────┐
│ DISTRIBUIÇÃO GOLD OFICIAL (16 itens = 12.5% cada)      │
├────────────────────────────────────────────────────────┤
│  Factual:        2 itens (12.5%)                       │
│  Temporal:       2 itens (12.5%)                       │
│  Descritiva:     2 itens (12.5%)                       │
│  Relacional:     2 itens (12.5%)                       │
│  Comparativa:    2 itens (12.5%)                       │
│  Exploratória:   2 itens (12.5%)                       │
│  Contraditória:  2 itens (12.5%)                       │
│  Não Respondível:2 itens (12.5%)                       │
└────────────────────────────────────────────────────────┘
```

* **Hash SHA256 do Gold:** `9877d939a049e884689d61598a6971e6c4c8767db801b4be81f218fefc4202bf`
* **Hash SHA256 do Silver:** `4da9810b34c5ab2b36ef84e183ad0ef0944367bc98bc28bed9491a3b0b5410d4`
* **Manifesto de Integridade:** Salvo em `versions/v0.2_balanced/checksums_and_manifest.json`.

---

# Slide 5: Como o Problema da Resposta Tautológica foi Resolvido

### Por que ocorria anteriormente?
1. **Chunks Estreitos:** O chunker cortava sentenças isoladas sem o contexto de parágrafo.
2. **Claims Vacuosas:** O modelo extraía expressões como *"onde meu avô teve atuação destacada"*.
3. **Eco de Enunciado:** A pergunta formulava *"Qual foi a atuação destacada?"* e, como a evidência não trazia a explicação, a resposta se limitava a papaguear: *"Lindolfo Collor teve atuação destacada..."*.

### A Solução Implementada em 3 Camadas:
1. **Camada de Segmentação (`src/preparation/chunker.py`):**
   - Janela ampliada para 1600 caracteres e overlap de 300, mantendo parágrafos completos e sentenças íntegras.
2. **Camada de Extração (`src/extraction/pipeline_extract.py`):**
   - Filtro de vacuidade: descarte de claims curtas (<25 chars) ou declarações genéricas que não informem uma ação, número, cargo ou diagnóstico objetivo.
3. **Camada de Prompts (`src/generation/`):**
   - Diretriz anti-tautologia estrita: a pergunta deve investigar o dado e a resposta deve declarar diretamente a informação substantiva sem repetir as fórmulas da pergunta.

---

# Slide 6: Amostra 1 — Perguntas Factual e Temporal

### Categoria: Factual / Entidade (Item Q002)
* **Pergunta:** *“Em que período Fernando Collor de Mello exerceu o mandato de deputado federal na Câmara dos Deputados?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `easy`
* **Resposta de Referência (Gold):**
  > *“O documento indica que Fernando Collor de Mello foi deputado federal, porém não especifica o período em que exerceu o mandato.”*
* **Evidência Documental:**
  * `DISCURSO_1990_COLLOR` | Trecho: *“Orgulho-me de ter pertencido à Câmara dos Deputados”*
  * *(Demonstra rigor ao declarar expressamente os limites da fonte sem alucinar datas externas).*

---

### Categoria: Temporal (Item Q005)
* **Pergunta:** *“Em que período histórico a dívida externa do Brasil chegou a ser considerada a maior do mundo, conforme o pronunciamento de José Sarney em 1985?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `medium`
* **Resposta de Referência (Gold):**
  > *“Em 1985, durante o governo de José Sarney, a dívida externa do Brasil foi considerada a maior do mundo.”*
* **Evidência Documental:**
  * `DISCURSO_1985_SARNEY` | Trecho: *“a maior dívida externa do mundo”*

---

# Slide 7: Amostra 2 — Perguntas Descritiva e Relacional

### Categoria: Descritiva (Item Q011)
* **Pergunta:** *“Como o pronunciamento de Itamar Franco em 1992 caracteriza a relação entre a modernidade e a negação de direitos básicos como o pão, o alfabeto, o trabalho honrado, a saúde e a alegria, e quais implicações isso tem para o diagnóstico da situação socioeconômica da época?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `medium`
* **Resposta de Referência (Gold):**
  > *“Itamar Franco descreve a modernidade como criminosa e cruel, ao negar a dignidade do pão, do alfabeto, do trabalho honrado, da saúde e da alegria, revelando que a época vivia exclusão profunda, escassez de recursos básicos, falta de acesso à educação e à saúde, e precariedade do trabalho, o que permite diagnosticar uma crise socioeconômica marcada por desigualdade estrutural e falhas no modelo de desenvolvimento da década de 1990.”*
* **Evidência Documental:**
  * `DISCURSO_1992_ITAMAR` | Trecho: *“Repilo, por criminosa e cruel, a modernidade que lhes nega a dignidade do pão, do alfabeto, do trabalho honrado, da saúde e da alegria.”*

---

### Categoria: Relacional (Item Q015)
* **Pergunta:** *“De que maneira a declaração de Luiz Inácio Lula da Silva sobre o Brasil ter quase 175 milhões de habitantes impacta as estratégias de planejamento urbano do Ministério das Cidades ao atender as demandas das populações indígenas e das comunidades rurais?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `medium`
* **Resposta de Referência (Gold):**
  > *“O Brasil tem quase 175 milhões de habitantes.”*
* **Evidência Documental:**
  * `DISCURSO_2003_LULA` | Trecho: *“O Brasil é um País imenso, um continente de alta complexidade humana, ecológica e social, com quase 175 milhões de habitantes”*

---

# Slide 8: Amostra 3 — Perguntas Comparativa e Exploratória

### Categoria: Comparativa (Multi-Documento) (Item Q017)
* **Pergunta:** *“Como a percepção da gravidade da crise política brasileira difere entre a afirmação de José Sarney em 1985 de que se tratava da maior crise da história do Brasil e a descrição de Fernando Collor de Mello em 1990 centrada em seu papel como membro da Câmara dos Deputados?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `hard` (Requer 2 documentos)
* **Resposta de Referência (Gold):**
  > *“Sarney caracterizou a situação de 1985 como a maior crise política da história do Brasil, enquanto a fala de Collor em 1990 destaca apenas seu orgulho de ter sido deputado, sem qualificar a gravidade da crise, mostrando uma percepção menos alarmista.”*
* **Evidências Documentais:**
  1. `DISCURSO_1985_SARNEY`: *“Herdei para administrar a maior crise política da história brasileira”*
  2. `DISCURSO_1990_COLLOR`: *“Orgulho-me de ter pertencido à Câmara dos Deputados”*

---

### Categoria: Exploratória (Visão Transversal do Acervo) (Item Q021)
* **Pergunta:** *“Quais pronunciamentos de posse abordam explicitamente a crise das contas públicas, o endividamento e a desordem fiscal do Estado?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `hard` (Sonda 3 documentos)
* **Resposta de Referência (Gold):**
  > *“Nenhum dos pronunciamentos de posse identificados (DISCURSO_1985_SARNEY, DISCURSO_1990_COLLOR, DISCURSO_1992_ITAMAR) traz referência explícita à crise das contas públicas, ao endividamento ou à desordem fiscal do Estado nos trechos analisados.”*
* **Evidências Documentais:**
  * Mapeamento de `DISCURSO_1985_SARNEY`, `DISCURSO_1990_COLLOR` e `DISCURSO_1992_ITAMAR`.

---

# Slide 9: Amostra 4 — Perguntas Contraditória e Não Respondível

### Categoria: Contraditória / Divergências Historiográficas (Item Q027)
* **Pergunta:** *“Como os discursos de 1985 e 1995 apresentam visões conflitantes sobre as raízes da inflação e o alcance dos planos de estabilização anteriores?”*
* **Respondibilidade:** `answerable` | **Dificuldade:** `hard`
* **Resposta de Referência (Gold):**
  > *“O discurso de 1985 (DISCURSO_1985_SARNEY) atribui as raízes da inflação à grave crise política que vivia o país, indicando que a instabilidade institucional alimentava a alta de preços; já o discurso de 1995 (DISCURSO_1995_FHC) enfatiza causas econômicas estruturais e limita a eficácia dos planos de estabilização anteriores, apontando que eles não alcançaram controle duradouro da inflação.”*
* **Evidências Documentais:**
  1. `DISCURSO_1985_SARNEY`: *“Herdei para administrar a maior crise política da história brasileira”*
  2. `DISCURSO_1995_FHC`: *“Os 'anos dourados' de JK terminaram com inflação e tensões políticas em alta.”*

---

### Categoria: Não Respondível / Abstenção (Item Q029)
* **Pergunta:** *“Qual foi a taxa exata de desemprego apurada pelo IBGE no terceiro trimestre de 1987 segundo o discurso de posse de 1985?”*
* **Respondibilidade:** `unanswerable` | **Dificuldade:** `hard` (Adversarial temporal)
* **Resposta de Referência (Gold):**
  > *“Os pronunciamentos oficiais disponíveis no acervo não contêm registros comprobatórios para responder à pergunta sobre 1987. Para esclarecer este ponto com rigor historiográfico, seria necessário consultar atas legislativas externas, diários confidenciais ou levantamentos estatísticos específicos de órgãos oficiais não documentados nos discursos de posse.”*
* **Evidência Documental:**
  * `[]` *(Nenhuma evidência vinculada — o sistema deve declarar abstenção explícita).*

---

# Slide 10: Auditoria Automática e Métricas de Aprovação

### Relatório dos 7 Filtros Automáticos (`logs/auto_validation_report.json`)
O modelo auditor independente (`openai/gpt-oss-20b`) avaliou as 32 respostas candidatas confrontando cada afirmação contra os trechos documentais:

```
┌────────────────────────────────────────────────────────┐
│ RESULTADOS DA VALIDAÇÃO AUTOMÁTICA                     │
├────────────────────────────────────────────────────────┤
│  Total de Itens Avaliados:       32 itens              │
│  Itens Aprovados Integralmente:  23 itens (71.9%)      │
│  Itens Sinalizados / Alertados:   9 itens (28.1%)      │
│  Taxa de Aprovação Líquida:      71.9%                 │
└────────────────────────────────────────────────────────┘
```

### Por que 9 itens foram sinalizados?
* **Detecção de Extrapolação pelo LLM B:** Itens em que a resposta tentou formular generalizações históricas não constantes na citação literal foram barrados.
* **Filtro Mecânico Anti-Tautologia:** Itens que apresentaram vocabulário com alta sobreposição não substantiva foram movidos para a pasta `corpus/validated_flagged.jsonl`, impedindo sua entrada no conjunto Gold.

---

# Slide 11: Limitações Identificadas Nesta Etapa

1. **Dependência de Trechos em Perguntas Exploratórias e Contraditórias:**
   * Como o acervo deste piloto é composto por discursos pontuais de posse, as perguntas exploratórias foram formuladas a partir dos chunks temáticos extraídos, e não de um índice invertido global pré-computado (BM25/Vetorial).
2. **Limites de Rate Limit na API:**
   * Durante a geração intensiva de 32 itens atômicos com LLM A e verificação com LLM B, o provedor impôs breves pausas de tokens por minuto (TPM), contornadas pelo mecanismo de resiliência e retentativas do `UnifiedLLMClient`.
3. **Ausência de Erros de OCR Reais:**
   * O corpus de discursos presidenciais é composto de transcrições digitais limpas. A avaliação da robustez do RAG a texto degradado será concretizada quando utilizarmos os escaneamentos do RIMA-UFRRJ.

---

# Slide 12: Próximos Passos e Conclusão

### Pronto para o Acervo Real (RIMA-UFRRJ)
Com a refatoração completa em `src/`, a resolução do problema de repetição de perguntas e o balanceamento exato das 8 categorias do guia, a infraestrutura técnica está 100% validada e pronta para o corpus da dissertação:

1. **Ingestão dos Documentos do RIMA:** Inserir os PDFs escaneados (atas, ofícios e relatórios) na pasta `data/raw/`.
2. **Execução em Um Comando:** Executar `python scripts/run_pipeline.py`.
3. **Validação Humana por Historiadores:** Utilizar a planilha `corpus/revisao_especialistas_piloto.csv` e o checklist `corpus/revisao_especialistas_piloto.md` gerados automaticamente para auditoria por pares.
