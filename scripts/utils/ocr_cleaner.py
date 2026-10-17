import re
from typing import Tuple


class OCRCleaner:
    @staticmethod
    def clean(text: str) -> Tuple[str, dict]:
        """Normaliza o texto e registra as alterações efetuadas."""
        original_len = len(text)
        
        # 1. Normalização de quebras de linha e tabs
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 2. Remoção de hifenização de fim de linha (ex.: pa- \n lavra)
        normalized = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", normalized)
        
        # 3. Normalização de espaços múltiplos consecutivos
        normalized = re.sub(r"[ \t]+", " ", normalized)
        
        # 4. Ajuste de pontuação com espaçamento inadequado
        normalized = re.sub(r"\s+([.,;:!?])", r"\1", normalized)
        
        # 5. Normalização de aspas
        normalized = normalized.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        
        cleaned = normalized.strip()
        
        stats = {
            "original_length": original_len,
            "cleaned_length": len(cleaned),
            "chars_removed": original_len - len(cleaned)
        }
        return cleaned, stats

    @staticmethod
    def estimate_quality(text: str) -> str:
        """Estima a qualidade do OCR / transcrição com base na proporção de caracteres estranhos."""
        if not text:
            return "noisy"
        
        # Caracteres de controle ou ruídos comuns de OCR
        weird_chars = len(re.findall(r"[^\w\s.,;:!?()\"'/\-–—%ºª§$]", text))
        ratio = weird_chars / len(text)
        
        if ratio < 0.01:
            return "good"
        elif ratio < 0.05:
            return "moderate"
        else:
            return "noisy"
