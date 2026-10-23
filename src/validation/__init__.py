"""Módulo de validação e auditoria."""
from src.validation.schema_validator import SchemaValidator
from src.validation.auto_validator import run_auto_validation

__all__ = ["SchemaValidator", "run_auto_validation"]
