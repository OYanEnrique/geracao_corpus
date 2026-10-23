"""Chunker contextual baseado em janelas de sentenças com rastreamento de offsets."""
import re
from typing import List, Dict, Any


class ContextualSentenceChunker:
    """Segmentador em janelas amplas de sentenças, preservando contexto temático e offsets."""

    def __init__(self, target_chars: int = 1600, overlap_chars: int = 300, min_chars: int = 400):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars
        self.min_chars = min_chars

    def split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Divide o texto em sentenças preservando os offsets originais globais."""
        sentences = []
        # Captura término de sentença preservando pontuações
        pattern = re.compile(r'([^.!?]+[.!?]+(?:\s+|$)|[^.!?]+$)')
        for match in pattern.finditer(text):
            sentence_text = match.group().strip()
            if sentence_text:
                sentences.append({
                    "text": sentence_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return sentences

    def chunk_document(self, doc_id: str, text: str, page: int = 1) -> List[Dict[str, Any]]:
        """Gera trechos preservando contexto suficiente para evitar perguntas tautológicas."""
        sentences = self.split_into_sentences(text)
        if not sentences:
            return []

        chunks = []
        chunk_idx = 1
        current_sentences = []
        current_len = 0

        i = 0
        while i < len(sentences):
            sent = sentences[i]
            sent_len = len(sent["text"])
            
            current_sentences.append(sent)
            current_len += sent_len

            # Se atingiu o tamanho alvo ou é a última sentença
            if current_len >= self.target_chars or i == len(sentences) - 1:
                chunk_text = " ".join([s["text"] for s in current_sentences])
                start_offset = current_sentences[0]["start"]
                end_offset = current_sentences[-1]["end"]
                
                chunk_id = f"{doc_id}_C{chunk_idx:03d}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "page": page,
                    "char_start": start_offset,
                    "char_end": end_offset,
                    "text": chunk_text,
                    "char_length": len(chunk_text),
                    "sentence_count": len(current_sentences)
                })
                chunk_idx += 1

                if i == len(sentences) - 1:
                    break

                # Overlap controlado
                overlap_acc = 0
                backtrack_count = 0
                for back_sent in reversed(current_sentences):
                    if overlap_acc + len(back_sent["text"]) <= self.overlap_chars:
                        overlap_acc += len(back_sent["text"])
                        backtrack_count += 1
                    else:
                        break

                current_sentences = []
                current_len = 0
                if backtrack_count > 0:
                    i = i - backtrack_count + 1
                else:
                    i += 1
            else:
                i += 1

        return chunks
