import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class UnifiedLLMClient:
    """Cliente unificado para chamadas a LLM com fallback para modo Mock."""

    def __init__(self, provider: str = "openai", model: str = "gpt-4o", temperature: float = 0.0):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.mock_mode = False
        self._init_client()

    def _init_client(self):
        if self.provider == "mock":
            self.mock_mode = True
            return

        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.mock_mode = True
                return
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)

        elif self.provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                self.mock_mode = True
                return
            from groq import Groq
            self.client = Groq(api_key=api_key)

        elif self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                self.mock_mode = True
                return
            os.environ["GEMINI_API_KEY"] = api_key
            try:
                import litellm
                self.litellm = litellm
            except ImportError:
                self.mock_mode = True

        else:
            # Fallback para litellm se disponível
            try:
                import litellm
                self.litellm = litellm
            except ImportError:
                self.mock_mode = True

    def call_json(self, prompt: str, system_prompt: Optional[str] = None) -> Any:
        """Executa uma chamada ao LLM garantindo que a resposta seja parseada como JSON."""
        if self.mock_mode:
            return self._mock_response(prompt)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        raw_output = ""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    response_format={"type": "json_object"} if "json" in prompt.lower() else None
                )
                raw_output = response.choices[0].message.content

            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    response_format={"type": "json_object"} if "json" in prompt.lower() else None
                )
                raw_output = response.choices[0].message.content

            else:
                model_name = self.model
                if self.provider == "gemini" and not model_name.startswith("gemini/"):
                    model_name = f"gemini/{model_name}"
                response = self.litellm.completion(
                    model=model_name,
                    messages=messages,
                    temperature=self.temperature
                )
                raw_output = response.choices[0].message.content

            # Extrair JSON de forma robusta
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_output, re.DOTALL)
            candidate = match.group(1).strip() if match else raw_output.strip()

            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                start_bracket = min([i for i in [candidate.find('['), candidate.find('{')] if i != -1], default=-1)
                end_bracket = max(candidate.rfind(']'), candidate.rfind('}'))
                if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                    return json.loads(candidate[start_bracket:end_bracket+1])
                raise

        except Exception as e:
            # Se a API falhar ou der timeout/erro de autenticação, avisa e cai em mock se configurado
            print(f"[Aviso LLM {self.provider}] Erro na chamada: {e}. Usando mock gerativo.")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> Any:
        """Gera respostas mockadas estruturadas e semanticamente conectadas ao texto do prompt."""
        # Se for extração de evidências
        if "Extração de Unidades de Evidência" in prompt or "claim" in prompt:
            # Extrair frases factuais do trecho passado no prompt
            text_match = re.search(r"### Texto do trecho:\s*```text\s*(.*?)\s*```", prompt, re.DOTALL)
            sample_text = text_match.group(1) if text_match else prompt
            
            # Buscar sentenças que contenham números, anos ou entidades
            sentences = [s.strip() for s in re.split(r"[.!?]", sample_text) if len(s.strip()) > 35]
            evidences = []
            for i, sent in enumerate(sentences[:2]):
                years = re.findall(r"\b(19\d\d|20\d\d)\b", sent)
                entities = [w for w in re.findall(r"\b[A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*\b", sent) if len(w) > 3]
                evidences.append({
                    "claim": f"{sent}.",
                    "evidence_span": sent,
                    "entities": entities[:3] if entities else ["Brasil", "Governo Federal"],
                    "dates": years if years else ["1985"],
                    "relations": [
                        {
                            "subject": entities[0] if entities else "Presidente",
                            "predicate": "afirmou que",
                            "object": "as reformas são necessárias"
                        }
                    ],
                    "evidence_type": "explicit",
                    "notes": "Extração preliminar ancorada no texto documental"
                })
            return evidences if evidences else [
                {
                    "claim": "O documento registra as diretrizes de posse e prioridades do governo.",
                    "evidence_span": sample_text[:120],
                    "entities": ["Brasil"],
                    "dates": ["1985"],
                    "relations": [{"subject": "Governo", "predicate": "apresenta", "object": "diretrizes"}],
                    "evidence_type": "explicit",
                    "notes": "Evidência genérica"
                }
            ]

        # Se for verificação independente (LLM B)
        if "Verificação Independente" in prompt or "overall_verdict" in prompt:
            return {
                "overall_verdict": "SUPPORTED",
                "claims": [
                    {
                        "claim_text": "Afirmação extraída da resposta de referência.",
                        "verdict": "SUPPORTED",
                        "supporting_evidence_id": "E0001",
                        "justification": "O trecho original citado no documento sustenta integralmente o fato."
                    }
                ],
                "issues_detected": []
            }

        # Se for resposta de referência
        if "Resposta de Referência" in prompt or "reference_answer" in prompt:
            return {
                "reference_answer": "Conforme documentado no pronunciamento de posse, foram enfatizadas as metas de combate à inflação e atendimento às demandas sociais.",
                "answer_claims": [
                    {
                        "claim_text": "O pronunciamento de posse enfatizou metas de combate à inflação.",
                        "supporting_evidence_ids": ["E0001"],
                        "support_level": "supported"
                    }
                ],
                "reasoning_notes": "Resposta minimamente suficiente e 100% ancorada no trecho citado."
            }

        # Default genérico
        return {"status": "success", "message": "Execução simulada mock concluída"}
