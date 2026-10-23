"""Validador de schemas JSON baseado em jsonschema Draft202012."""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import jsonschema


class SchemaValidator:
    def __init__(self, schemas_dir: str = "corpus/schemas"):
        self.schemas_dir = Path(schemas_dir)
        self.schemas: Dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self):
        if not self.schemas_dir.exists():
            return
        for schema_file in self.schemas_dir.glob("*.json"):
            name = schema_file.stem.replace("_schema", "")
            with open(schema_file, "r", encoding="utf-8") as f:
                self.schemas[name] = json.load(f)

    def validate(self, schema_name: str, instance: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Valida uma instância contra o schema correspondente."""
        if schema_name not in self.schemas:
            raise ValueError(f"Schema '{schema_name}' não encontrado em {self.schemas_dir}.")

        validator = jsonschema.Draft202012Validator(self.schemas[schema_name])
        errors = [err.message for err in validator.iter_errors(instance)]
        return len(errors) == 0, errors
