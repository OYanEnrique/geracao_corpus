"""Módulo de geração de perguntas e respostas."""
from src.generation.question_generator import run_question_generation
from src.generation.answer_generator import run_answer_generation

__all__ = ["run_question_generation", "run_answer_generation"]
