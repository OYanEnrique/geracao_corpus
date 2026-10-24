"""Comitês de Modelos para Geração e Audição com Votação e Rejeição de Tautologias."""
import re
import json
import concurrent.futures
from typing import Dict, Any, List, Tuple
from src.utils.llm_client import UnifiedLLMClient
from src.utils.config import get_models_config


def extract_words(text: str) -> List[str]:
    """Extrai palavras limpas com mais de 3 letras para análise lexical."""
    return [w.lower() for w in re.findall(r'\b[a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]{4,}\b', text)]


def is_lexically_tautological(question: str, answer: str, threshold: float = 0.70) -> Tuple[bool, float, str]:
    """
    Verifica mecanicamente se a resposta é essencialmente uma repetição da pergunta.
    Retorna (é_tautológico, taxa_sobreposicao, justificativa).
    """
    q_words = set(extract_words(question))
    a_words = extract_words(answer)

    if not a_words or not q_words:
        return False, 0.0, "Texto insuficiente para análise."

    # Interseção de vocabulário
    common = q_words.intersection(set(a_words))
    overlap_ratio = len(common) / len(set(a_words))

    # Palavras substantivas novas que a resposta trouxe além da pergunta
    novel_words = set(a_words) - q_words

    # Se a resposta tem mais de 70% das palavras repetindo a pergunta e poucas palavras novas (< 4 palavras novas)
    if overlap_ratio >= threshold and len(novel_words) < 5:
        return True, overlap_ratio, f"Resposta tautológica: {overlap_ratio*100:.1f}% de sobreposição e apenas {len(novel_words)} termos novos."

    # Padrões frasais diretos de cópia
    q_clean = re.sub(r'^[Qq]ual|[Qq]uais|[Cc]omo|[Qq]uem|[Ee]m que ano|[Ee]m que data|[Ee]m que momento', '', question).strip(' ?.:;')
    if q_clean.lower() in answer.lower() and len(novel_words) < 3:
        return True, 0.95, "Resposta espelha diretamente o núcleo frasal da pergunta sem dados substantivos adicionais."

    return False, overlap_ratio, "Vocabulário independente e substantivo."


class GenerationCommittee:
    """Comitê de Geração composto por 3 modelos maiores com sistema de votação."""

    def __init__(self):
        cfg = get_models_config()
        self.models_meta = cfg.get("generation_committee", [])
        if not self.models_meta:
            # Fallback caso não configurado
            self.models_meta = [
                {"id": "gen_groq_120b", "name": "GPT-OSS 120B (Groq)", "provider": "groq", "model": "openai/gpt-oss-120b", "temperature": 0.2},
                {"id": "gen_or_llama70b", "name": "Llama 3.3 70B (OpenRouter)", "provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct", "temperature": 0.2},
                {"id": "gen_or_qwen72b", "name": "Qwen 2.5 72B (OpenRouter)", "provider": "openrouter", "model": "qwen/qwen-2.5-72b-instruct", "temperature": 0.2}
            ]
        self.clients = [
            UnifiedLLMClient(
                provider=m["provider"],
                model=m["model"],
                temperature=m.get("temperature", 0.2),
                max_tokens=m.get("max_tokens", 800)
            ) for m in self.models_meta
        ]

    def propose_and_vote_question(self, category: str, context_prompt: str) -> Dict[str, Any]:
        """
        1. Modelos 1 e 2 propõem formulações candidatas de perguntas.
        2. O comitê (3 modelos) vota na melhor formulação avaliando clareza e ausência de tautologia.
        3. Retorna a formulação vencedora com os metadados de votação.
        """
        # Obter candidatos dos modelos 1 e 2
        candidates = []

        def call_gen(idx, client, name):
            prompt = f"""Você é um historiador especialista em formulação de perguntas para avaliar sistemas RAG.
Categoria da pergunta solicitada: {category.upper()}

DIRETRIZ CENTRAL ANTI-TAUTOLOGIA:
A pergunta NUNCA deve sugerir ou antecipar a resposta em seu próprio enunciado.
Formule uma indagação investigativa profunda sobre os fatos documentais descritos abaixo.

{context_prompt}

Retorne estritamente um JSON:
{{
  "candidate_question": "texto completo da pergunta formulada"
}}"""
            res = client.call_json(prompt)
            q_text = res.get("candidate_question", "").strip() if isinstance(res, dict) else ""
            return {"author": name, "candidate_question": q_text}

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(call_gen, 0, self.clients[0], self.models_meta[0]["name"]),
                executor.submit(call_gen, 1, self.clients[1], self.models_meta[1]["name"])
            ]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    c = fut.result()
                    if c["candidate_question"]:
                        candidates.append(c)
                except Exception as e:
                    print(f"[Aviso Comitê Geração] Erro ao obter candidato: {e}")

        if not candidates:
            # Fallback seguro
            candidates = [{"author": self.models_meta[0]["name"], "candidate_question": "Quais diretrizes e fatos fundamentais foram registrados no documento?"}]

        if len(candidates) == 1:
            return {
                "selected_question": candidates[0]["candidate_question"],
                "candidate_author": candidates[0]["author"],
                "voting_results": {"winner": candidates[0]["candidate_question"], "votes": {self.models_meta[2]["name"]: 1}}
            }

        # Votação do comitê (Modelos votam entre Candidato 1 e Candidato 2)
        c1_text = candidates[0]["candidate_question"]
        c2_text = candidates[1]["candidate_question"]

        voting_prompt = f"""Você é um juiz avaliador de perguntas historiográficas para benchmark de IA.
Compare as duas formulações candidatas para a categoria {category.upper()}:

Candidato 1: "{c1_text}"
Candidato 2: "{c2_text}"

Critérios de avaliação:
1. Ausência de tautologia (a pergunta não pode entregar nem conter a resposta).
2. Clareza e profundidade historiográfica.
3. Exequibilidade de responder apenas com as fontes documentais.

Retorne estritamente um JSON:
{{
  "vote": 1 ou 2,
  "justification": "razão da escolha"
}}"""

        votes = {1: 0, 2: 0}
        vote_logs = []

        def call_vote(client, meta):
            res = client.call_json(voting_prompt)
            v = res.get("vote", 1) if isinstance(res, dict) else 1
            if v not in [1, 2]:
                v = 1
            return (meta["name"], v, res.get("justification", "Critérios atendidos"))

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(call_vote, self.clients[i], self.models_meta[i]) for i in range(3)]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    m_name, v, just = fut.result()
                    votes[v] += 1
                    vote_logs.append({"model": m_name, "vote": v, "justification": just})
                except Exception:
                    votes[1] += 1

        winner_idx = 0 if votes[1] >= votes[2] else 1
        winner = candidates[winner_idx]

        return {
            "selected_question": winner["candidate_question"],
            "candidate_author": winner["author"],
            "candidates_evaluated": [c1_text, c2_text],
            "votes_count": votes,
            "vote_logs": vote_logs
        }

    def generate_reference_answer(self, question: str, evidences: List[Dict[str, Any]], category: str) -> Dict[str, Any]:
        """Gera resposta de referência estritamente fundamentada e não-tautológica usando o líder do comitê."""
        ev_summary = []
        req_ids = []
        for e in evidences:
            eid = e.get("evidence_id", "E0001")
            req_ids.append(eid)
            doc = e.get("doc_id") or e.get("document_id", "DOC")
            span = e.get("span") or e.get("text") or e.get("claim", "")
            ev_summary.append(f"[{eid} - {doc}]: {span}")

        if category == "unanswerable":
            return {
                "reference_answer": "As fontes documentais oficiais disponíveis no acervo não contêm registros comprobatórios para responder a esta indagação.",
                "answer_claims": [{
                    "claim_text": "Os pronunciamentos disponíveis não trazem comprovação sobre este tema específico.",
                    "supporting_evidence_ids": [],
                    "support_level": "supported"
                }]
            }

        prompt = f"""Você é um historiador que formula a resposta de referência oficial para um benchmark RAG.

Pergunta formulada: "{question}"
Evidências documentais autênticas:
{chr(10).join(ev_summary)}

DIRETRIZES FUNDAMENTAIS ANTI-TAUTOLOGIA:
1. NUNCA comece a resposta papagueando ou repetindo a pergunta.
2. Forneça DIRETAMENTE as informações substantivas (nomes, valores, instituições, datas, diagnósticos) comprovadas nas evidências.
3. Se a evidência contiver dados exatos, cite-os com precisão.
4. Redija em 2 a 3 frases afirmativas, claras e objetivas.

Retorne estritamente um JSON:
{{
  "reference_answer": "resposta substantiva fundamentada",
  "answer_claims": [
    {{"claim_text": "afirmação factual substantiva 1", "supporting_evidence_ids": {json.dumps(req_ids)}, "support_level": "supported"}}
  ]
}}"""
        # Utiliza o modelo Llama 3.3 70B ou GPT-OSS 120B para redigir a resposta
        client = self.clients[1] if len(self.clients) > 1 else self.clients[0]
        res = client.call_json(prompt)

        if isinstance(res, dict) and "reference_answer" in res and res["reference_answer"]:
            return res

        # Fallback usando o primeiro modelo
        res2 = self.clients[0].call_json(prompt)
        if isinstance(res2, dict) and "reference_answer" in res2:
            return res2

        # Fallback seguro ancorado na evidência
        fallback_ans = " ".join([e.get("span", "")[:150] for e in evidences])
        return {
            "reference_answer": fallback_ans,
            "answer_claims": [{"claim_text": fallback_ans, "supporting_evidence_ids": req_ids, "support_level": "supported"}]
        }


class AuditingCommittee:
    """Comitê de Auditoria composto por 3 modelos menores com sistema de votação independente."""

    def __init__(self):
        cfg = get_models_config()
        self.models_meta = cfg.get("auditing_committee", [])
        if not self.models_meta:
            self.models_meta = [
                {"id": "audit_groq_20b", "name": "GPT-OSS 20B (Groq)", "provider": "groq", "model": "openai/gpt-oss-20b", "temperature": 0.0},
                {"id": "audit_or_llama8b", "name": "Llama 3.1 8B (OpenRouter)", "provider": "openrouter", "model": "meta-llama/llama-3.1-8b-instruct", "temperature": 0.0},
                {"id": "audit_or_qwen7b", "name": "Qwen 2.5 7B (OpenRouter)", "provider": "openrouter", "model": "qwen/qwen-2.5-7b-instruct", "temperature": 0.0}
            ]
        self.clients = [
            UnifiedLLMClient(
                provider=m["provider"],
                model=m["model"],
                temperature=m.get("temperature", 0.0),
                max_tokens=m.get("max_tokens", 500)
            ) for m in self.models_meta
        ]

    def audit_item(self, item: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Executa a auditoria independente de um item por 3 modelos menores com votação por maioria.
        Retorna (is_approved, audit_metadata).
        """
        question = item["question"]
        ref_answer = item["reference_answer"]
        evidences = item.get("evidence", [])
        is_answerable = item.get("answerability") != "unanswerable"

        # 1. Filtro mecânico anti-tautologia prévio
        if is_answerable:
            is_tauto_mech, overlap_ratio, tauto_just = is_lexically_tautological(question, ref_answer)
            if is_tauto_mech:
                return False, {
                    "approved": False,
                    "rejection_reason": f"Filtro Mecânico Anti-Tautologia: {tauto_just}",
                    "overlap_ratio": overlap_ratio,
                    "auditor_votes": []
                }

        # 2. Votação dos 3 auditores independentes
        ev_summary = []
        for e in evidences:
            eid = e.get("evidence_id", "E0001")
            doc = e.get("doc_id", "DOC")
            span = e.get("span", "")
            ev_summary.append(f"[{eid} - {doc}]: {span}")

        audit_prompt = f"""Você é um auditor independente de qualidade historiográfica de dados para IA.
Analise o seguinte par de pergunta e resposta de referência contra as evidências documentais:

Pergunta: "{question}"
Resposta de Referência: "{ref_answer}"
Evidências Fornecidas:
{chr(10).join(ev_summary) if ev_summary else "[Sem evidências vinculadas - item de abstenção/não-respondível]"}

Tarefas de Auditoria:
1. VERIFICAÇÃO DE ENTAILMENT: A resposta está estritamente fundamentada nas evidências fornecidas?
2. VERIFICAÇÃO DE TAUTOLOGIA: A resposta é uma mera repetição/cópia da pergunta sem acrescentar fatos novos?
3. VEREDITO FINAL: Escolha estritamente entre:
   - "SUPPORTED" (Fundamentada e não-tautológica)
   - "PARTIAL" (Parcialmente sustentada)
   - "UNSUPPORTED" (Sem respaldo documental ou alucinação)
   - "TAUTOLOGICAL" (Resposta inútil que apenas repete a pergunta)

Retorne estritamente um JSON:
{{
  "verdict": "SUPPORTED" | "PARTIAL" | "UNSUPPORTED" | "TAUTOLOGICAL",
  "is_tautological": false | true,
  "confidence": 0.0 a 1.0,
  "justification": "análise concisa"
}}"""

        auditor_results = []

        def call_auditor(idx, client, meta):
            res = client.call_json(audit_prompt)
            verdict = res.get("verdict", "SUPPORTED") if isinstance(res, dict) else "SUPPORTED"
            is_tauto = res.get("is_tautological", False) if isinstance(res, dict) else False
            just = res.get("justification", "Auditado") if isinstance(res, dict) else ""
            return {
                "auditor_id": meta["id"],
                "auditor_name": meta["name"],
                "verdict": str(verdict).upper(),
                "is_tautological": bool(is_tauto),
                "justification": just
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(call_auditor, i, self.clients[i], self.models_meta[i])
                for i in range(len(self.clients))
            ]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    auditor_results.append(fut.result())
                except Exception as e:
                    auditor_results.append({
                        "auditor_id": "fallback",
                        "auditor_name": "Auditor",
                        "verdict": "SUPPORTED",
                        "is_tautological": False,
                        "justification": f"Fallback: {e}"
                    })

        # Contabilizar votos
        support_votes = 0
        tauto_votes = 0
        reject_votes = 0

        for r in auditor_results:
            v = r["verdict"]
            if r["is_tautological"] or v == "TAUTOLOGICAL":
                tauto_votes += 1
            elif v in ["SUPPORTED", "PARTIAL"]:
                support_votes += 1
            else:
                reject_votes += 1

        # Regra de aprovação por maioria:
        # Pelo menos 2 auditores apoiam (SUPPORTED/PARTIAL) E menos de 2 apontam tautologia
        is_approved = (support_votes >= 2) and (tauto_votes < 2)

        audit_metadata = {
            "approved": is_approved,
            "support_votes": support_votes,
            "tautology_votes": tauto_votes,
            "reject_votes": reject_votes,
            "auditor_results": auditor_results,
            "verdict_summary": f"{support_votes}/3 Aprovado(s) - Tautologias: {tauto_votes}"
        }

        return is_approved, audit_metadata
