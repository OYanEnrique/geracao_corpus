"""Cliente unificado de LLM com suporte a Groq, Gemini, OpenAI e fallback mock."""
import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class UnifiedLLMClient:
    """Cliente unificado para chamadas a LLM com suporte robusto a extração de JSON."""

    def __init__(self, provider: str = "groq", model: str = "openai/gpt-oss-120b", temperature: float = 0.0):
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
            try:
                import litellm
                self.litellm = litellm
            except ImportError:
                self.mock_mode = True

    def call_json(self, prompt: str, system_prompt: Optional[str] = None) -> Any:
        """Executa chamada ao LLM garantindo que a resposta seja parseada como JSON."""
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

            # Extração robusta de JSON
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
            print(f"[Aviso LLM {self.provider}] Erro na chamada: {e}. Usando fallback.")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> Any:
        """Gera resposta simulada contextualizada caso API esteja inacessível."""
        if "Extração" in prompt or "claim" in prompt:
            return [{
                "claim": "O documento histórico registra prioridades e diretrizes administrativas.",
                "evidence_span": "As mudanças começaram e continuarão.",
                "entities": ["Brasil"],
                "dates": ["1985"],
                "relations": [{"subject": "Governo", "predicate": "apresenta", "object": "diretrizes"}],
                "evidence_type": "explicit",
                "notes": "Fallback"
            }]

        if "overall_verdict" in prompt:
            return {
                "overall_verdict": "SUPPORTED",
                "claims": [{
                    "claim_text": "Afirmação validada contra as evidências.",
                    "verdict": "SUPPORTED",
                    "supporting_evidence_id": "E0001",
                    "justification": "Comprovada pelo trecho documental."
                }],
                "issues_detected": []
            }

        if "reference_answer" in prompt or "Resposta de Referência" in prompt:
            return {
                "reference_answer": "As fontes documentais confirmam o diagnóstico apresentado.",
                "answer_claims": [{
                    "claim_text": "As fontes confirmam o diagnóstico apresentado.",
                    "supporting_evidence_ids": ["E0001"],
                    "support_level": "supported"
                }],
                "reasoning_notes": "Sustentada pelas fontes."
            }

        return {"status": "success"}
