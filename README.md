# Geração de Corpus Semissintético de QA para RAG Verificável em Acervos Históricos

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Repository](https://img.shields.io/badge/GitHub-OYanEnrique%2Fgeracao__corpus-blue?logo=github)](https://github.com/OYanEnrique/geracao_corpus)

Pipeline reprodutível para construção, validação e congelamento de benchmarks semissintéticos de perguntas, respostas e evidências documentais ancoradas. Desenvolvido no âmbito do Mestrado em Humanidades Digitais para avaliação de sistemas de **Geração Aumentada por Recuperação (RAG) Verificável** aplicados a acervos históricos.

---

## 📌 Contexto e Fundamentação

Sistemas RAG convencionais frequentemente falham diante de documentos históricos:
- Alucinam datas, nomes e relações causais;
- Produzem citações genéricas que não sustentam a afirmação proferida;
- Eliminam ambiguidades documentais essenciais à crítica historiográfica;
- Fornecem respostas categóricas quando deveriam se abster por insuficiência das fontes.

Para contornar essas fragilidades, este projeto implementa um princípio metodológico estrito:

> **A evidência documental precede a pergunta ($D \to E \to Q \to A$).**  
> O modelo de linguagem nunca inventa a verdade de referência; cada afirmação de resposta é rastreável a um trecho textual literal (*claim-level grounding*), incluindo casos controlados de **abstenção** (*unanswerable questions*) e perguntas **multi-documento**.

---

## 🏗️ Arquitetura do Pipeline

O pipeline opera em etapas desacopladas com separação formal de papéis entre dois modelos de IA:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   01_prepare    │ ───> │   02_extract    │ ───> │  03_generate_q  │
│  Ingestão &     │      │   Evidências    │      │    Perguntas    │
│  Segmentação    │      │    Atômicas     │      │   (LLM A)       │
└─────────────────┘      └─────────────────┘      └────────┬────────┘
                                                           │
┌─────────────────┐      ┌─────────────────┐               │
│  06_human_eval  │ <─── │  05_validate    │ <─── 04_generate_a  │
│  Revisão com    │      │  Auditoria A/B  │      Respostas Gold   │
│  Historiadores  │      │  7 Filtros Auto │      (LLM A)          │
└────────┬────────┘      └─────────────────┘      └────────────────┘
         │
         ▼
┌─────────────────┐
│  07_gold_silver │ ───> Benchmark Congelado com Hash SHA256 (versions/v0.1_pilot1/)
│  Particionamento│
└─────────────────┘
```

- **LLM A (Gerador):** Formula perguntas e respostas estritamente limitadas às evidências extraídas.
- **LLM B (Auditor Independente):** Modelo independente que avalia o *entailment* e reprova extrapolações ou inferências indevidas.

---

## 📂 Estrutura de Diretórios

```
geracao_corpus/
├── config/
│   ├── pipeline.yaml                  # Parâmetros de chunking, amostragem e thresholds
│   └── models.yaml                    # Configuração de provedores e modelos (Groq, OpenAI, Gemini)
├── contexto/
│   ├── guia_construcao_corpus_qa_historico.pdf
│   ├── proposta_rag_verificavel_acervos_historicos.pdf
│   └── plano_implementacao_corpus_qa.md # Plano de implementação completo
├── corpus/
│   ├── schemas/                       # Schemas formais JSON Schema (Draft 2020-12)
│   │   ├── document_schema.json
│   │   ├── evidence_schema.json
│   │   └── question_schema.json
│   ├── documents.jsonl                # Registro dos documentos catalogados
│   ├── chunks.jsonl                   # Trechos segmentados com controle de caracteres
│   ├── evidences.jsonl                # Evidências atômicas validadas
│   ├── questions_gold.jsonl           # Benchmark Gold oficial congelado
│   ├── questions_silver.jsonl         # Conjunto Silver auxiliar de desenvolvimento
│   ├── revisao_especialistas_piloto.md# Protocolo de validação com checklist para historiadores
│   └── revisao_especialistas_piloto.csv
├── data/
│   └── raw/
│       └── piloto_1/                  # Corpus de teste (discursos presidenciais 1985-2023)
├── logs/
│   └── auto_validation_report.json   # Relatório de aprovação/rejeição dos 7 filtros
├── prompts/                           # Prompts operacionais versionados
│   ├── evidence_extraction.md
│   ├── question_generation.md
│   ├── answer_generation.md
│   └── verification.md
├── scripts/                           # Pipeline sequencial executável
│   ├── 01_prepare_documents.py        # Limpeza e chunking sensível a sentenças
│   ├── 02_extract_evidences.py        # Extração de unidades de evidência (LLM A)
│   ├── 03_generate_questions.py       # Geração híbrida (factual, multi-doc, abstenção)
│   ├── 04_generate_answers.py         # Respostas de referência minimamente suficientes
│   ├── 05_auto_validate.py            # Validação automática e auditoria cruzada (LLM B)
│   ├── 06_human_review_export.py      # Exportação para análise qualitativa de historiadores
│   ├── 07_build_gold_silver.py        # Separação balanceada e congelamento SHA256
│   └── utils/                         # Chunker, limpador de OCR, validador de schema e LLM client
├── versions/
│   └── v0.1_pilot1/                   # Benchmark imutável com checksums_and_manifest.json
├── .env.example                       # Modelo de variáveis de ambiente
├── relatorio.md                       # Apresentação executiva em formato de slides
└── README.md                          # Documentação do projeto
```

---

## 🚀 Como Utilizar

### 1. Clonar o Repositório

```bash
git clone https://github.com/OYanEnrique/geracao_corpus.git
cd geracao_corpus
```

### 2. Configurar o Ambiente Virtual

Recomenda-se Python 3.10 ou superior:

```bash
# Criar e ativar o ambiente virtual
python -m venv venv

# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# No Linux/macOS:
source venv/bin/activate
```

Instale as dependências necessárias:

```bash
pip install -r requirements.txt
```
*(Ou instale diretamente os pacotes principais: `pydantic jsonschema groq litellm pyyaml python-dotenv`)*

### 3. Configurar Chaves de API

Copie o arquivo de exemplo e insira suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env`:
```env
# Provedor recomendado no piloto (rápido e com modelos abertos de ponta)
GROQ_API_KEY=gsk_suachaveaqui

# Outros provedores opcionais suportados:
GEMINI_API_KEY=
OPENAI_API_KEY=
```

Os modelos ativos podem ser ajustados em `config/models.yaml`:
```yaml
llm_generator:
  provider: "groq"
  model: "openai/gpt-oss-120b"

llm_verifier:
  provider: "groq"
  model: "openai/gpt-oss-20b"
```

---

## ⚡ Execução do Pipeline

Os scripts são modulares e podem ser executados em sequência:

```bash
# Etapa 1 & 2: Ingestão, limpeza textual e segmentação de sentenças
python scripts/01_prepare_documents.py

# Etapa 3: Extração de evidências atômicas ancoradas
python scripts/02_extract_evidences.py

# Etapa 4: Geração híbrida de perguntas (factuais, comparativas e abstenção)
python scripts/03_generate_questions.py

# Etapa 5: Geração de respostas de referência atômicas (Gold Answers)
python scripts/04_generate_answers.py

# Etapa 6: Validação automática (7 filtros estruturais + auditoria com LLM B)
python scripts/05_auto_validate.py

# Etapa 7: Exportação de tabelas de revisão para especialistas humanos
python scripts/06_human_review_export.py

# Etapa 8: Particionamento balanceado e congelamento de versão (SHA256)
python scripts/07_build_gold_silver.py
```

---

## 🧪 Piloto 1 — Dados e Resultados

O pipeline foi validado sobre um corpus de **12 discursos presidenciais brasileiros pós-redemocratização (1985–2023)**, com o objetivo de testá-lo.

### Resultados Obtidos:
- **12 documentos** processados e catalogados;
- **215 chunks** com janelas de sentenças e contagem precisa de caracteres;
- **109 evidências atômicas** extraídas e validadas contra schema estrito;
- **34 itens de benchmark** gerados (single-doc, multi-doc e pares adversariais $Q+/Q-$);
- **88.2% de aprovação automática** pelo modelo auditor (`openai/gpt-oss-20b`), que reprovou 4 itens por inferência interpretativa indevida;
- **Benchmark Gold congelado** em `versions/v0.1_pilot1/` com integridade criptográfica SHA256.

Para uma visão aprofundada do piloto, consulte o arquivo [`relatorio.md`](relatorio.md).

---

## 📋 Critérios de Aceitação de um Item Gold

Um item só é admitido no conjunto Gold definitivo se satisfizer todos os requisitos:
1. **Clareza Contextual:** A pergunta é formulada em linguagem natural histórica e não depende de contexto implícito ausente;
2. **Provenance Exata:** Cada evidência aponta para `document_id`, `page` (ou offset de caracteres) e `span` textual literal;
3. **Derivabilidade Estrita:** A resposta é 100% derivável das evidências citadas, sem inclusão de fatos externos;
4. **Decomposição em Afirmações:** Cada sentença da resposta possui um identificador de suporte (`supporting_evidence_ids`);
5. **Auditoria Cruzada A/B:** O modelo verificador confirmou a sustentação (*SUPPORTED*);
6. **Revisão Humana:** Historiador especialista aprovou a plausibilidade da pesquisa e a veracidade documental.

---

## 👤 Autor

**Yan Enrique**  
- GitHub: [@OYanEnrique](https://github.com/OYanEnrique)  
- Mestrando em Humanidades Digitais — Universidade Federal Rural do Rio de Janeiro (UFRRJ)
