# Plano de Implementação — Corpus Semissintético de QA para RAG Verificável em Acervos Históricos

> Derivado do *Guia Metodológico de Construção do Corpus* e da *Proposta de Dissertação: RAG verificável para pesquisa em acervos históricos*.

---

## Sumário

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura do Pipeline](#2-arquitetura-do-pipeline)
3. [Fase 0 — Infraestrutura e Ambiente](#3-fase-0--infraestrutura-e-ambiente)
4. [Fase 1 — Seleção e Amostragem dos Documentos](#4-fase-1--seleção-e-amostragem-dos-documentos)
5. [Fase 2 — Preparação e Segmentação dos Documentos](#5-fase-2--preparação-e-segmentação-dos-documentos)
6. [Fase 3 — Extração de Unidades de Evidência](#6-fase-3--extração-de-unidades-de-evidência)
7. [Fase 4 — Geração de Perguntas](#7-fase-4--geração-de-perguntas)
8. [Fase 5 — Geração de Respostas de Referência](#8-fase-5--geração-de-respostas-de-referência)
9. [Fase 6 — Validação Automática](#9-fase-6--validação-automática)
10. [Fase 7 — Validação Humana por Especialistas](#10-fase-7--validação-humana-por-especialistas)
11. [Fase 8 — Separação Gold / Silver e Congelamento](#11-fase-8--separação-gold--silver-e-congelamento)
12. [Schemas JSON](#12-schemas-json)
13. [Prompts Operacionais](#13-prompts-operacionais)
14. [Controle de Qualidade e Auditorias](#14-controle-de-qualidade-e-auditorias)
15. [Cronograma de Execução](#15-cronograma-de-execução)
16. [Critérios de Aceitação de um Item Gold](#16-critérios-de-aceitação-de-um-item-gold)
17. [Conexão com a Avaliação do RAG](#17-conexão-com-a-avaliação-do-rag)
18. [Riscos e Mitigações](#18-riscos-e-mitigações)
19. [Checklist Geral de Implementação](#19-checklist-geral-de-implementação)

---

## 1. Visão Geral do Projeto

### 1.1. Objetivo

Construir um **benchmark semissintético** de perguntas históricas, respostas de referência e evidências documentais, adequado para avaliar de forma granular um sistema RAG verificável aplicado a acervos históricos (RIMA-UFRRJ).

### 1.2. Princípio Central

> **As perguntas podem ser geradas com LLMs, mas cada resposta de referência deve estar vinculada a evidências reais do acervo. O LLM não deve "inventar" a verdade de referência.**

### 1.3. Unidade Mínima do Benchmark

Cada item do benchmark é composto por:

| Componente | Descrição |
|---|---|
| **Pergunta (Q)** | Pergunta de pesquisa histórica em linguagem natural |
| **Resposta de referência (A)** | Resposta minimamente suficiente e completamente sustentada |
| **Evidência(s) (E)** | Trechos documentais específicos com localização precisa |
| **Metadados** | Tipo de pergunta, dificuldade, respondibilidade, qualidade de OCR |

### 1.4. Fluxo Conceitual

```
Acervo → Documentos (D) → Evidências (E) → Perguntas (Q) → Respostas de referência (A)
                                                                    ↓
                                                        Verificação automática
                                                                    ↓
                                                          Revisão humana
                                                                    ↓
                                                          Gold / Silver
                                                                    ↓
                                                       Experimentos de RAG
```

### 1.5. Metas Quantitativas

| Conjunto | Quantidade de itens | Nível de validação |
|---|---|---|
| **Gold** | 80–100 itens | Revisados detalhadamente por especialistas |
| **Silver** | 300–500 itens | Gerados e verificados automaticamente |
| **Documentos indexados** | 300–1.000 | Conforme extensão da coleção |

---

## 2. Arquitetura do Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PIPELINE COMPLETO                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │ Etapa 1  │──>│   Etapa 2    │──>│   Etapa 3    │                │
│  │ Seleção  │   │ Preparação   │   │ Extração de  │                │
│  │ de Docs  │   │ de Documentos│   │ Evidências   │                │
│  └──────────┘   └──────────────┘   └──────┬───────┘                │
│                                           │                         │
│                                           ▼                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │   Etapa 6    │<──│   Etapa 5    │<──│   Etapa 4    │            │
│  │  Validação   │   │  Resposta de │   │  Geração de  │            │
│  │  Automática  │   │  Referência  │   │  Perguntas   │            │
│  └──────┬───────┘   └──────────────┘   └──────────────┘            │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐   ┌──────────────┐                                │
│  │   Etapa 7    │──>│   Etapa 8    │                                │
│  │  Validação   │   │ Gold/Silver  │                                │
│  │  Humana      │   │ Congelamento │                                │
│  └──────────────┘   └──────────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Regra operacional:** A evidência de referência deve existir antes da pergunta. Em perguntas multi-documento, todas as evidências necessárias devem ser registradas explicitamente.

---

## 3. Fase 0 — Infraestrutura e Ambiente

### 3.1. Estrutura de Diretórios

```
dissertacao_rag_hd/
├── contexto/                       # Documentos de referência e este plano
├── data/
│   ├── raw/                        # Documentos originais (PDF/imagens)
│   ├── ocr_original/               # Texto OCR bruto
│   ├── ocr_clean/                  # Texto OCR pós-limpeza
│   └── metadata/                   # Metadados por documento (JSON)
├── corpus/
│   ├── documents.jsonl             # Registro de todos os documentos
│   ├── chunks.jsonl                # Trechos segmentados com provenance
│   ├── evidences.jsonl             # Unidades de evidência extraídas
│   ├── questions_silver.jsonl      # Itens Silver
│   ├── questions_gold.jsonl        # Itens Gold (congelado antes dos experimentos)
│   └── schemas/                    # Schemas JSON de validação
│       ├── document_schema.json
│       ├── evidence_schema.json
│       └── question_schema.json
├── prompts/
│   ├── evidence_extraction.md      # Prompt de extração de evidências
│   ├── question_generation.md      # Prompt de geração de perguntas
│   ├── answer_generation.md        # Prompt de geração de respostas
│   └── verification.md             # Prompt de verificação independente
├── scripts/
│   ├── 01_prepare_documents.py     # Preparação e segmentação
│   ├── 02_extract_evidences.py     # Extração de evidências
│   ├── 03_generate_questions.py    # Geração de perguntas
│   ├── 04_generate_answers.py      # Geração de respostas de referência
│   ├── 05_auto_validate.py         # Validação automática
│   ├── 06_human_review_export.py   # Exportação para revisão humana
│   ├── 07_build_gold_silver.py     # Construção dos conjuntos finais
│   └── utils/
│       ├── ocr_cleaner.py
│       ├── chunker.py
│       ├── deduplicator.py
│       └── schema_validator.py
├── evaluation/                     # Avaliação do RAG (pós-benchmark)
├── notebooks/                      # Análises exploratórias
├── config/
│   ├── models.yaml                 # Configuração dos modelos usados
│   └── pipeline.yaml               # Parâmetros do pipeline
├── logs/                           # Logs de execução
└── versions/                       # Versionamento do corpus
    ├── v0.1_pilot1/
    ├── v0.2_pilot2/
    └── v1.0_gold_frozen/
```

### 3.2. Dependências Técnicas

| Componente | Tecnologia sugerida | Propósito |
|---|---|---|
| Linguagem | Python 3.10+ | Código do pipeline |
| LLM gerador (LLM A) | GPT-4o / Claude 3.5 Sonnet | Extração de evidências, geração de Q&A |
| LLM verificador (LLM B) | Modelo diferente do gerador | Verificação independente (entailment) |
| OCR | Tesseract / easyOCR / OCR do acervo | Extração textual dos documentos |
| Embeddings | sentence-transformers / OpenAI | Para detecção de duplicatas e distância lexical |
| Validação JSON | jsonschema / pydantic | Validação estrutural dos itens |
| Armazenamento | JSONL + Git | Versionamento e rastreabilidade |
| Revisão humana | Planilha estruturada / Label Studio | Interface para validadores |

### 3.3. Tarefas de Setup

- [ ] Criar repositório Git com a estrutura de diretórios acima
- [ ] Configurar ambiente Python com dependências
- [ ] Configurar acesso às APIs de LLM (gerador e verificador)
- [ ] Definir e versionar schemas JSON (ver Seção 12)
- [ ] Criar arquivo `config/pipeline.yaml` com parâmetros iniciais
- [ ] Configurar `.gitignore` (excluir dados brutos pesados, manter schemas e prompts)

---

## 4. Fase 1 — Seleção e Amostragem dos Documentos

### 4.1. Objetivo

Definir a subcoleção do RIMA-UFRRJ que será utilizada, garantindo diversidade documental suficiente sem ampliar o escopo a ponto de dificultar a validação humana.

### 4.2. Critérios de Seleção da Coleção

| Critério | Descrição |
|---|---|
| Coleção específica | Uma tipologia documental relativamente homogênea (ex.: atas, relatórios, correspondências) |
| Período definido | Recorte temporal claro e documentável |
| Condições de acesso | Direitos de uso e reprodução confirmados |
| Volume adequado | 300–1.000 documentos para indexação |
| Qualidade de OCR | Variada (documentos com boa e baixa qualidade) |

### 4.3. Critérios de Amostragem para o Benchmark

Selecionar **100–150 documentos** para a fase de geração de itens, garantindo:

- [ ] Diferentes períodos cronológicos relevantes
- [ ] Diferentes tipos documentais dentro da coleção
- [ ] Documentos com OCR de **boa** e de **baixa** qualidade
- [ ] Documentos **curtos** e **extensos**
- [ ] Documentos com **alta** e **baixa** densidade de entidades, datas e eventos
- [ ] Documentos com possíveis **divergências** ou **lacunas** informacionais

### 4.4. Entregáveis

| Artefato | Formato | Descrição |
|---|---|---|
| `corpus/documents.jsonl` | JSONL | Registro de todos os documentos selecionados |
| Documento de justificativa | Markdown | Critérios de seleção e decisões tomadas |
| Mapa da amostra | Tabela | Distribuição por tipo, período, qualidade de OCR |

### 4.5. Tarefas

- [ ] Identificar coleções candidatas no RIMA-UFRRJ
- [ ] Confirmar condições de acesso e direitos
- [ ] Catalogar documentos disponíveis (tipo, período, extensão, qualidade de OCR)
- [ ] Selecionar subcoleção principal
- [ ] Amostrar 100–150 documentos com diversidade controlada
- [ ] Registrar cada documento com identificador persistente

---

## 5. Fase 2 — Preparação e Segmentação dos Documentos

### 5.1. Objetivo

Transformar cada documento em trechos processáveis, preservando identificação, localização e versões do texto (OCR original e limpo).

### 5.2. Processamento por Documento

Para cada documento, preservar:

| Campo | Descrição |
|---|---|
| `document_id` | Identificador único e persistente |
| `collection` | Coleção de origem |
| `doc_type` | Tipologia documental (ata, relatório, ofício, etc.) |
| `date` | Data do documento (quando disponível) |
| `author` | Autoria ou responsável |
| `page_count` | Número de páginas |
| `ocr_original` | Texto OCR bruto, por página |
| `ocr_clean` | Texto OCR limpo, por página |
| `image_refs` | Referência à imagem original de cada página |
| `archival_context` | Informações arquivísticas (fundo, série, etc.) |

### 5.3. Segmentação (Chunking)

A segmentação deve equilibrar contexto e granularidade:

| Parâmetro | Valor sugerido | Observação |
|---|---|---|
| Tamanho base | 300–500 tokens | Avaliar experimentalmente |
| Overlap | 50–100 tokens | Para preservar contexto entre trechos |
| Preservação de limites | Parágrafos e sentenças | Não cortar no meio de frases |

Cada **chunk** deve manter:

```json
{
  "chunk_id": "ATA_023_C004",
  "document_id": "ATA_023",
  "page_start": 3,
  "page_end": 4,
  "char_start": 1200,
  "char_end": 1890,
  "text_clean": "...",
  "text_original": "...",
  "ocr_quality_estimate": "good"
}
```

### 5.4. Limpeza de OCR

A limpeza deve ser **controlada e registrada**:

- Corrigir erros evidentes de OCR (caracteres trocados, espaçamento)
- **Sempre** manter a versão original para comparação
- Registrar quais correções foram aplicadas
- Não "inventar" texto em trechos ilegíveis — marcar como `[ilegível]`

### 5.5. Tarefas

- [ ] Implementar script `01_prepare_documents.py`
- [ ] Extrair OCR de todos os documentos selecionados (se necessário)
- [ ] Aplicar limpeza de OCR preservando versão original
- [ ] Segmentar documentos em chunks
- [ ] Estimar qualidade de OCR por trecho (`good` / `moderate` / `noisy`)
- [ ] Validar preservação de identificadores e localização (page, char_start/end)
- [ ] Gerar `corpus/chunks.jsonl` com todos os trechos

---

## 6. Fase 3 — Extração de Unidades de Evidência

### 6.1. Objetivo

A partir dos trechos, identificar **unidades de evidência** atômicas que possam dar origem a perguntas. A evidência é o alicerce de todo o benchmark.

### 6.2. Tipos de Evidência a Extrair

| Tipo | Exemplos |
|---|---|
| Afirmações factuais | Nomeações, funcionamento, existência de cursos, problemas registrados |
| Entidades | Pessoas, instituições, cargos, localidades |
| Datas e períodos | Datas explícitas, intervalos, sequência de eventos |
| Relações | Pessoa-cargo, pessoa-instituição, evento-local |
| Eventos | Criação, inauguração, encerramento, mudança administrativa |
| Avaliações documentais | Críticas, justificativas, descrições de problemas |
| Contradições potenciais | Datas divergentes, nomes distintos, versões incompatíveis |
| Lacunas | Informações sugeridas pelo contexto mas não documentadas |

### 6.3. Schema da Unidade de Evidência

```json
{
  "evidence_id": "E0042",
  "document_id": "ATA_023",
  "chunk_id": "ATA_023_C004",
  "page": 4,
  "text": "...existência de disciplinas sem docentes designados...",
  "claim": "Havia disciplinas sem professores designados em 1950.",
  "entities": ["Escola", "docentes"],
  "dates": ["1950"],
  "relations": [{"subject": "disciplinas", "predicate": "sem", "object": "docentes"}],
  "evidence_type": "explicit",
  "ocr_quality": "good",
  "notes": ""
}
```

> **Importante:** Guardar sempre o trecho original (`text`) e a localização documental. A `claim` normalizada pelo LLM é útil, mas **nunca deve substituir** a evidência textual original.

### 6.4. Regras de Extração

1. Extrair **apenas** afirmações explicitamente sustentadas pelo trecho
2. Não usar conhecimento externo
3. Não completar lacunas — marcar como `evidence_type: "ambiguous"` ou `"gap"`
4. Cada evidência deve ser atômica (uma afirmação verificável)
5. Registrar contradições potenciais entre documentos diferentes

### 6.5. Prompt de Extração (LLM A)

Ver Seção 13.1 para o prompt completo.

### 6.6. Tarefas

- [ ] Implementar script `02_extract_evidences.py`
- [ ] Refinar prompt de extração com 10–20 documentos piloto
- [ ] Executar extração em todos os trechos da amostra
- [ ] Validar cobertura dos tipos de evidência
- [ ] Identificar contradições entre documentos
- [ ] Gerar `corpus/evidences.jsonl`
- [ ] Verificar que todo `evidence_id` tem `document_id`, `page` e `text` válidos

---

## 7. Fase 4 — Geração de Perguntas

### 7.1. Objetivo

Gerar perguntas diversas em linguagem natural, ancoradas nas evidências extraídas. A geração deve ser **híbrida**: combinando múltiplas estratégias.

### 7.2. Estratégias de Geração

#### 7.2.1. Perguntas derivadas de uma única evidência

Adequadas para itens factuais, temporais e descritivos. Testam recuperação direta e precisão das citações.

> **Exemplo:**
> - Evidência: *"Em março de 1950 permaneciam sem professores as disciplinas de Agronomia e Zootecnia."*
> - Pergunta: *Quais disciplinas estavam sem professores em março de 1950?*
> - Resposta: *Agronomia e Zootecnia.*

#### 7.2.2. Perguntas multi-documento

Exigem duas ou mais evidências de documentos distintos. Testam recuperação, agregação e capacidade de não fundir fatos indevidamente.

> **Meta:** 30–40% do conjunto Gold deve exigir mais de uma evidência ou mais de um documento.

#### 7.2.3. Geração a partir de entidades e relações

Usar a extração prévia de entidades para criar perguntas sistemáticas:

```
Pessoa: João Silva | Cargo: Diretor | Instituição: Escola Agrícola | Ano: 1951
→ "Quem era diretor da Escola Agrícola em 1951?"
→ "Qual cargo João Silva ocupava em 1951?"
→ "A qual instituição João Silva estava vinculado?"
```

#### 7.2.4. Templates + paráfrase por LLM

Templates controlam a estrutura; o LLM fornece variação linguística:

| Template |
|---|
| `Quem foi [CARGO] de [INSTITUIÇÃO] em [ANO]?` |
| `Como [DOC_A] e [DOC_B] descrevem [EVENTO]?` |
| `Quais documentos mencionam [ENTIDADE]?` |

Após instanciar: pedir ao LLM 2–3 paráfrases semanticamente equivalentes.

### 7.3. Perguntas Adversariais e de Abstenção

O benchmark **precisa** conter perguntas sem resposta suficiente. Sem elas, não se avalia o mecanismo de abstenção.

| Tipo adversarial | Construção | Comportamento esperado |
|---|---|---|
| Informação ausente | Perguntar por valor/causa não presente | Abster-se ou indicar insuficiência |
| Premissa falsa | Inserir dado incompatível com a fonte | Corrigir a premissa e não aceitá-la |
| Causalidade não sustentada | Transformar associação em causa | Responder com ressalva ou abster-se |
| Contradição entre fontes | Selecionar duas fontes divergentes | Preservar a divergência |
| Hard negative temporal | Trocar o ano por um muito próximo | Não transferir resposta para ano errado |
| Hard negative de entidade | Trocar pessoa/instituição por entidade semelhante | Não completar por plausibilidade |

#### 7.3.1. Pares respondível × não respondível

Estratégia eficiente: criar pares controlados onde a versão negativa altera apenas um elemento:

| Q+ (respondível) | Q− (não respondível) |
|---|---|
| Em que ano a escola iniciou suas atividades? | Qual foi a principal motivação pessoal do diretor para iniciar as atividades? |
| Quanto a instituição recebeu em 1951? | Quanto a instituição recebeu em 1952? *(se 1952 não está documentado)* |

### 7.4. Taxonomia das Perguntas

Cada pergunta deve ser classificada em múltiplas dimensões:

| Dimensão | Valores possíveis |
|---|---|
| **Tipo primário** | factual / temporal / descritiva / relacional / comparativa / exploratória / contraditória |
| **Fonte** | single-document / multi-document |
| **Evidência** | explicit / implicit-supported / partial / contradictory / absent |
| **Respondibilidade** | answerable / partial / unanswerable |
| **OCR** | clean / moderate / noisy |
| **Distância lexical** | low / medium / high |
| **Raciocínio** | lookup / temporal / relation / aggregation / comparison / contradiction |
| **Dificuldade** | easy / medium / hard |

### 7.5. Distribuição Sugerida para 80 Itens Gold

| Categoria principal | Quantidade |
|---|---|
| Factual / entidade | 15 |
| Temporal | 10 |
| Descritiva | 10 |
| Relacional | 10 |
| Comparativa / multi-documento | 15 |
| Exploratória | 5 |
| Contraditória | 5 |
| Não respondível | 10 |
| **Total** | **80** |

### 7.6. Níveis de Saída Esperada

| Rótulo | Condição | Gold answer |
|---|---|---|
| `SUPPORTED` | Evidência suficiente e adequada | Resposta direta com citação |
| `PARTIAL` | Há indícios, mas falta sustentação completa | Resposta limitada e explicitamente qualificada |
| `CONTRADICTORY` | Fontes divergem | Apresentar as versões e citar cada fonte |
| `UNANSWERABLE` | Evidência ausente ou insuficiente | Abstenção explícita e justificativa documental |

### 7.7. Tarefas

- [ ] Implementar script `03_generate_questions.py` com as 4 estratégias
- [ ] Gerar perguntas single-document a partir das evidências
- [ ] Identificar pares de evidências para perguntas multi-documento
- [ ] Gerar perguntas a partir de entidades e relações
- [ ] Instanciar templates e gerar paráfrases
- [ ] Construir itens adversariais e de abstenção (pares Q+/Q−)
- [ ] Classificar cada pergunta nas dimensões da taxonomia
- [ ] Verificar distribuição e balanceamento

---

## 8. Fase 5 — Geração de Respostas de Referência

### 8.1. Objetivo

Produzir a **gold answer** para cada pergunta: uma resposta minimamente suficiente e completamente sustentada pelas evidências.

### 8.2. Regras para a Gold Answer

1. **Uma afirmação por sentença** sempre que isso facilitar a associação com evidências
2. **Não introduzir** explicações históricas que não estejam documentadas
3. Em **contradições**: citar explicitamente cada versão
4. Em **respostas parciais**: indicar exatamente qual parte está sustentada e qual não está
5. Em **abstenções**: informar o tipo de evidência que seria necessário localizar

### 8.3. Teste de Verificação Rápida

> *"Se eu remover do sistema todo conhecimento externo e deixar apenas as evidências registradas neste item, ainda é possível produzir a gold answer?"*
>
> Se a resposta for **não**, o item precisa ser corrigido.

### 8.4. Tarefas

- [ ] Implementar script `04_generate_answers.py`
- [ ] Gerar respostas candidatas usando LLM A com as evidências como contexto único
- [ ] Aplicar o teste de verificação rápida em cada item
- [ ] Segmentar respostas em afirmações verificáveis
- [ ] Mapear cada afirmação da resposta a um `evidence_id` específico

---

## 9. Fase 6 — Validação Automática

### 9.1. Objetivo

Filtrar itens problemáticos antes da revisão humana, reduzindo custo e esforço do especialista.

### 9.2. Filtros Automáticos

| # | Verificação | Tipo |
|---|---|---|
| 1 | Todos os `document_id`, páginas e trechos citados existem | Estrutural |
| 2 | Cada pergunta possui ao menos uma evidência (exceto `unanswerable`) | Estrutural |
| 3 | Detecção de perguntas duplicadas ou quase duplicadas | Semântico |
| 4 | A resposta não contém nomes, datas ou números ausentes das evidências | Factual |
| 5 | Segundo modelo (LLM B) julga entailment entre evidência e resposta | Semântico |
| 6 | Divergências entre o modelo gerador e o modelo verificador são sinalizadas | Cross-check |
| 7 | Itens com evidência truncada, ambígua ou mal localizada são rejeitados | Qualidade |

### 9.3. Separação de Funções entre Modelos

```
LLM A  →  gera pergunta e resposta candidata
LLM B  →  verifica se a resposta é sustentada pela evidência
Regras →  validam IDs, páginas, spans e metadados
Especialista → valida o item final
```

> **Motivo:** Evitar que o mesmo modelo gere e aprove o próprio erro. Modelos diferentes não eliminam o problema, mas reduzem self-consistency enganosa e tornam o processo mais auditável.

### 9.4. Classificação pelo LLM B (Verificação)

Para cada afirmação da resposta, o verificador deve classificar:

| Classificação | Descrição |
|---|---|
| `SUPPORTED` | A afirmação está integralmente sustentada pela evidência |
| `PARTIAL` | Parcialmente sustentada — faltam elementos |
| `CONTRADICTORY` | A evidência contradiz a afirmação |
| `UNSUPPORTED` | A afirmação introduz informação não presente nas evidências |

### 9.5. Tarefas

- [ ] Implementar script `05_auto_validate.py`
- [ ] Implementar verificações estruturais (IDs, páginas, spans)
- [ ] Implementar detecção de duplicatas (embeddings + similaridade coseno)
- [ ] Implementar verificação de entailment com LLM B
- [ ] Gerar relatório de validação com flags para cada item
- [ ] Separar itens em: `aprovado`, `requer_revisão`, `rejeitado`
- [ ] Registrar todas as divergências entre LLM A e LLM B

---

## 10. Fase 7 — Validação Humana por Especialistas

### 10.1. Objetivo

Historiadores ou especialistas no acervo revisam os itens candidatos que passaram pela validação automática.

### 10.2. Checklist de Validação Humana

Para cada item, o especialista deve avaliar:

- [ ] A pergunta é plausível para uma pesquisa histórica real?
- [ ] A resposta está integralmente sustentada pelas evidências indicadas?
- [ ] A formulação elimina alguma ambiguidade relevante existente na fonte?
- [ ] A resposta introduz causalidade, intenção ou interpretação não documentada?
- [ ] As citações apontam para as páginas corretas?
- [ ] Pergunta marcada como `unanswerable`: é realmente não respondível no corpus?
- [ ] Em contradições: todas as versões documentais relevantes foram preservadas?
- [ ] O item é difícil por razões historiograficamente legítimas, e não por má redação?

### 10.3. Formato de Revisão

Cada item deve ser apresentado ao revisor com:

1. A pergunta
2. A resposta candidata
3. As evidências (com links para o documento e página original)
4. Os metadados (tipo, dificuldade, respondibilidade)
5. O resultado da verificação automática

O revisor pode: **aprovar**, **corrigir**, **reclassificar** ou **rejeitar** o item.

### 10.4. Tarefas

- [ ] Implementar script `06_human_review_export.py` (exportar para planilha ou Label Studio)
- [ ] Definir protocolo de revisão com os especialistas
- [ ] Preparar material de treinamento para os revisores
- [ ] Executar rodada de revisão
- [ ] Incorporar correções ao corpus
- [ ] Registrar taxa de concordância inter-avaliadores (se mais de um revisor)

---

## 11. Fase 8 — Separação Gold / Silver e Congelamento

### 11.1. Definição

| Conjunto | Construção | Uso recomendado |
|---|---|---|
| **Gold** | 80–100 itens revisados detalhadamente por especialistas | Resultados principais da dissertação; comparação final entre sistemas |
| **Silver** | Centenas de itens gerados e verificados automaticamente | Desenvolvimento; testes de recuperação; análise de robustez |

> **Regra:** Não misturar itens Silver na avaliação final sem identificá-los. A força do trabalho está em ter um conjunto Gold pequeno, controlado e auditável.

### 11.2. Divisão Experimental — Evitar Vazamento

A divisão deve considerar **documentos**, não apenas perguntas:

- [ ] Split por documento ou grupo de documentos relacionados
- [ ] Perguntas de ajuste de prompts separadas do conjunto Gold de teste
- [ ] **Congelar o Gold antes de executar os experimentos finais**
- [ ] Versionar corpus, índice, prompts e modelos usados

### 11.3. Tarefas

- [ ] Implementar script `07_build_gold_silver.py`
- [ ] Selecionar itens Gold a partir dos aprovados na revisão humana
- [ ] Verificar distribuição por tipo, dificuldade e respondibilidade
- [ ] Separar conjuntos por documento (evitar vazamento)
- [ ] Congelar versão Gold em `versions/v1.0_gold_frozen/`
- [ ] Gerar `corpus/questions_gold.jsonl` e `corpus/questions_silver.jsonl`
- [ ] Registrar hash de integridade dos conjuntos finais

---

## 12. Schemas JSON

### 12.1. Schema do Documento

```json
{
  "document_id": "string (único)",
  "collection": "string",
  "doc_type": "string (ata | relatório | ofício | ...)",
  "title": "string (opcional)",
  "date": "string (ISO 8601 ou aproximado)",
  "author": "string (opcional)",
  "page_count": "integer",
  "ocr_quality_overall": "string (good | moderate | noisy)",
  "archival_context": "string",
  "file_ref": "string (caminho para o arquivo original)"
}
```

### 12.2. Schema da Evidência

```json
{
  "evidence_id": "string (E0001, E0002, ...)",
  "document_id": "string (FK → documento)",
  "chunk_id": "string (FK → chunk)",
  "page": "integer",
  "text": "string (trecho original do documento)",
  "claim": "string (afirmação normalizada)",
  "entities": ["string"],
  "dates": ["string"],
  "relations": [{"subject": "string", "predicate": "string", "object": "string"}],
  "evidence_type": "string (explicit | implicit | ambiguous | gap)",
  "ocr_quality": "string (good | moderate | noisy)",
  "notes": "string (opcional)"
}
```

### 12.3. Schema do Item de Benchmark (Pergunta + Resposta + Evidência)

```json
{
  "id": "string (Q001, Q002, ...)",
  "question": "string",
  "primary_type": "string (factual | temporal | descriptive | relational | comparative | exploratory | contradictory)",
  "reasoning": "string (lookup | temporal | relation | aggregation | comparison | contradiction)",
  "source_type": "string (single_document | multi_document)",
  "answerability": "string (answerable | partial | unanswerable)",
  "reference_answer": "string",
  "answer_claims": [
    {
      "claim_text": "string",
      "supporting_evidence_ids": ["string"],
      "support_level": "string (supported | partial | contradictory | unsupported)"
    }
  ],
  "evidence": [
    {
      "evidence_id": "string",
      "doc_id": "string",
      "page": "integer",
      "span": "string"
    }
  ],
  "required_documents": "integer",
  "temporal_scope": "string (ex: 1948-1952)",
  "ocr_quality": "string (good | moderate | noisy)",
  "lexical_distance": "string (low | medium | high)",
  "difficulty": "string (easy | medium | hard)",
  "generation_model": "string (modelo usado para gerar)",
  "verification_model": "string (modelo usado para verificar)",
  "verification_result": "string (supported | partial | contradictory | unsupported)",
  "validation_status": "string (auto_only | human_validated | rejected)",
  "set": "string (gold | silver)",
  "validator_id": "string (opcional, ID do revisor humano)",
  "validator_notes": "string (opcional)",
  "created_at": "string (ISO 8601)",
  "version": "string"
}
```

---

## 13. Prompts Operacionais

### 13.1. Prompt — Extração de Evidências

```markdown
## Instrução

Você receberá um trecho documental histórico com identificador e página.

Extraia apenas afirmações explicitamente sustentadas pelo trecho.

Para cada afirmação, retorne um objeto JSON com:
- `claim`: afirmação factual normalizada
- `evidence_span`: trecho literal do documento que sustenta a afirmação
- `entities`: lista de entidades mencionadas (pessoas, instituições, cargos, localidades)
- `dates`: datas ou períodos mencionados
- `relations`: relações identificadas (subject, predicate, object)
- `evidence_type`: "explicit" | "implicit" | "ambiguous"

### Regras
- Não use conhecimento externo.
- Não complete lacunas com suposições.
- Se algo for ambíguo, marque como "ambiguous" e explique na nota.
- Cada afirmação deve ser atômica e verificável.

## Entrada

Documento: {document_id}
Página: {page}
Trecho:
---
{text}
---
```

### 13.2. Prompt — Geração de Perguntas

```markdown
## Instrução

Com base somente nas evidências fornecidas, gere perguntas de pesquisa em linguagem natural.

Para cada pergunta, indique:
- `question`: a pergunta
- `required_evidence_ids`: quais evidence_ids são necessários para respondê-la
- `primary_type`: factual | temporal | relational | comparative | descriptive | exploratory
- `reasoning`: lookup | temporal | relation | aggregation | comparison
- `difficulty`: easy | medium | hard
- `source_type`: single_document | multi_document

### Regras
- Gere itens de tipos variados.
- Não gere perguntas cuja resposta exija conhecimento externo.
- Para perguntas multi-documento, indique TODOS os evidence_ids necessários.
- Inclua variação linguística — evite que todas as perguntas tenham a mesma estrutura.

## Evidências fornecidas

{evidences_json}
```

### 13.3. Prompt — Geração de Resposta de Referência

```markdown
## Instrução

Com base SOMENTE nas evidências fornecidas, produza a resposta de referência para a pergunta.

### Regras
- Use apenas informações presentes nas evidências.
- Separe a resposta em afirmações verificáveis (uma por sentença).
- Para cada afirmação, indique o evidence_id que a sustenta.
- Não adicione conhecimento externo ou interpretações não documentadas.
- Se a evidência é parcial, diga explicitamente o que está sustentado e o que não está.
- Se a evidência é contraditória, apresente todas as versões com suas fontes.
- Se a evidência é insuficiente, indique abstenção e o que seria necessário buscar.

## Pergunta

{question}

## Evidências

{evidences_json}
```

### 13.4. Prompt — Verificação Independente (LLM B)

```markdown
## Instrução

Receba: pergunta, resposta candidata e evidências.

Para cada afirmação da resposta:
1. Identifique a afirmação
2. Localize a evidência que a sustenta (se houver)
3. Classifique como:
   - SUPPORTED: integralmente sustentada
   - PARTIAL: parcialmente sustentada
   - CONTRADICTORY: contradita pela evidência
   - UNSUPPORTED: informação não presente nas evidências

### Saída esperada
```json
{
  "overall_verdict": "SUPPORTED | PARTIAL | CONTRADICTORY | UNSUPPORTED",
  "claims": [
    {
      "claim_text": "...",
      "verdict": "SUPPORTED",
      "supporting_evidence_id": "E0042",
      "justification": "..."
    }
  ],
  "issues": ["lista de problemas identificados"]
}
```

## Entrada

Pergunta: {question}
Resposta candidata: {reference_answer}
Evidências: {evidences_json}
```

---

## 14. Controle de Qualidade e Auditorias

### 14.1. Auditorias Obrigatórias

| Auditoria | Pergunta de controle | Quando executar |
|---|---|---|
| **Cobertura** | Os principais tipos de pergunta estão representados? | Após geração |
| **Balanceamento** | Há itens fáceis e difíceis; respondíveis e não respondíveis? | Após geração |
| **Proveniência** | Toda evidência é rastreável à página e ao documento? | Após extração |
| **Sustentação** | Toda afirmação da gold answer está apoiada? | Após verificação |
| **Diversidade lexical** | Existem paráfrases e perguntas que não copiam literalmente a fonte? | Após geração |
| **Hard negatives** | Há casos em que pequenas mudanças tornam a pergunta não respondível? | Após geração |
| **OCR** | Há itens suficientes para medir efeito de ruído de OCR? | Após curadoria |

### 14.2. Métricas de Qualidade do Pipeline

| Métrica | Alvo |
|---|---|
| % itens com todas as referências válidas | 100% |
| % itens com verificação cruzada LLM A ↔ LLM B concordante | > 85% |
| % itens Gold aprovados na revisão humana (sobre candidatos) | > 65% |
| % de itens multi-documento no Gold | 30–40% |
| % de itens não respondíveis no Gold | ~12% (10/80) |
| Distribuição de dificuldade | Easy ~25%, Medium ~50%, Hard ~25% |

---

## 15. Cronograma de Execução

### 15.1. Fases Incrementais

| Fase | Atividade | Duração estimada | Saída principal |
|---|---|---|---|
| **Piloto 1** | Selecionar 10–20 documentos; extrair evidências; gerar 20 perguntas | 2 semanas | Validar prompts, schema e granularidade |
| **Piloto 2** | Adicionar multi-documento e perguntas adversariais | 1–2 semanas | Verificar se o sistema mede abstenção e contradição |
| **Silver** | Executar geração em lote e filtros automáticos | 2–3 semanas | 300–500 itens candidatos |
| **Curadoria** | Selecionar itens por cobertura, dificuldade e diversidade | 1 semana | 120–150 itens para revisão |
| **Gold** | Revisão por especialistas e correções finais | 2–3 semanas | 80–100 itens auditáveis |
| **Congelamento** | Versionar e bloquear conjunto final | 1 dia | Benchmark final para experimentos |

### 15.2. Alinhamento com o Cronograma da Dissertação (24 meses)

| Período da dissertação | Atividade do corpus |
|---|---|
| Meses 1–3 | Revisão bibliográfica, escolha da coleção, **Pilotos 1 e 2** |
| Meses 4–6 | Preparação do corpus e das evidências, **Silver e Curadoria** |
| Meses 7–9 | Implementação das buscas, **Gold e Congelamento** |
| Meses 10–15 | Implementação e experimentos do RAG (corpus já congelado) |
| Meses 16–18 | Experimentos e análise quantitativa |
| Meses 19–24 | Avaliação com especialistas, redação e defesa |

---

## 16. Critérios de Aceitação de um Item Gold

Um item só é aceito no conjunto Gold se **todos** os critérios forem atendidos:

- [ ] A pergunta é clara e não depende de contexto ausente
- [ ] As evidências necessárias estão identificadas e localizáveis (document_id, page, span)
- [ ] A gold answer é derivável **apenas** dessas evidências
- [ ] O rótulo de respondibilidade é justificável
- [ ] O tipo e a dificuldade da pergunta foram anotados
- [ ] Não há informação acrescentada por conhecimento externo do LLM
- [ ] O item passou por verificação automática (LLM B)
- [ ] O item passou por revisão humana
- [ ] O item não duplica semanticamente outro item do conjunto Gold

---

## 17. Conexão com a Avaliação do RAG

O mesmo item do benchmark permite avaliar diferentes componentes da arquitetura RAG:

| Componente avaliado | Campo do benchmark utilizado |
|---|---|
| **Recuperação** | `evidence.doc_id`, `page`, `span` |
| **Reranking** | Ordem das evidências relevantes recuperadas |
| **Resposta** | `reference_answer` e rótulo de sustentação |
| **Citação** | Mapeamento afirmação → `evidence_id` |
| **Abstenção** | `answerability` e condição esperada |
| **Robustez a OCR** | `ocr_quality` |
| **Análise por dificuldade** | `difficulty`, `reasoning`, `lexical_distance` |

### Configurações a Comparar

| Sistema | Componentes | Papel |
|---|---|---|
| **A — LLM sem recuperação** | Conhecimento paramétrico apenas | Controle |
| **B — RAG convencional** | Busca vetorial + primeiros trechos | Linha de base |
| **C — RAG verificável** | Busca híbrida + reranker + citação por afirmação + verificação + abstenção | **Proposta principal** |

> O benchmark permite medir **onde** o sistema falhou: recuperação, seleção, geração, citação, verificação ou decisão de se abster.

---

## 18. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| OCR de baixa qualidade impede extração de evidências | Evidências incompletas ou incorretas | Manter versão original + limpa; anotar `ocr_quality`; incluir itens com OCR ruidoso no benchmark |
| LLM inventa evidências ou respostas | Benchmark comprometido | Separar LLM gerador (A) e verificador (B); validação humana obrigatória para Gold |
| Documentos insuficientes para perguntas multi-doc | Benchmark com pouca diversidade | Garantir amostra com sobreposição temática/temporal entre documentos |
| Revisores humanos indisponíveis | Gold atrasado | Começar com piloto pequeno; preparar material de treinamento antecipadamente |
| Vazamento de dados entre dev e test | Resultados inflados | Split por documento, não por pergunta; congelar Gold antes dos experimentos |
| Auto-consistência enganosa do LLM | Itens incorretos passam validação | Usar modelos diferentes para geração e verificação; flag divergências |
| Escopo cresce além do gerenciável | Atraso no cronograma | Manter 80–100 itens Gold como meta fixa; Silver é incremental |

---

## 19. Checklist Geral de Implementação

### Infraestrutura
- [ ] Repositório Git criado com estrutura de diretórios
- [ ] Ambiente Python configurado com dependências
- [ ] APIs de LLM configuradas (gerador e verificador)

### Schemas e Configuração
- [ ] Schema JSON do documento definido e versionado
- [ ] Schema JSON da evidência definido e versionado
- [ ] Schema JSON do item de benchmark definido e versionado
- [ ] Arquivo de configuração do pipeline (`pipeline.yaml`)

### Dados
- [ ] Coleção-piloto definida e documentos elegíveis identificados
- [ ] OCR extraído e limpo com versão original preservada
- [ ] Documentos segmentados em chunks com provenance

### Pipeline de Geração
- [ ] Extração de evidências implementada e testada
- [ ] Geração de perguntas (4 estratégias) implementada
- [ ] Geração de respostas de referência implementada
- [ ] Hard negatives e itens de abstenção construídos

### Validação
- [ ] Validação automática implementada (7 filtros)
- [ ] Verificação cruzada LLM A ↔ LLM B implementada
- [ ] Protocolo de revisão humana definido
- [ ] Formato de exportação para revisores pronto

### Conjuntos Finais
- [ ] Conjunto Silver gerado e verificado automaticamente
- [ ] Conjunto Gold revisado por especialistas
- [ ] Gold congelado antes dos experimentos finais
- [ ] Hash de integridade registrado

### Documentação
- [ ] Prompts versionados junto ao corpus
- [ ] Critérios de validação documentados
- [ ] Modelos usados na geração e verificação registrados
- [ ] Schema, prompts, versão do corpus prontos para publicação junto à dissertação

---

> **Última atualização:** Outubro de 2026
>
> **Status:** Plano inicial — pronto para execução do Piloto 1
