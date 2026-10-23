"""Módulo de carregamento e gerenciamento de configurações."""
from pathlib import Path
from typing import Any, Dict
import yaml


def load_yaml_config(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_pipeline_config(config_path: str = "config/pipeline.yaml") -> Dict[str, Any]:
    return load_yaml_config(config_path)


def get_models_config(config_path: str = "config/models.yaml") -> Dict[str, Any]:
    return load_yaml_config(config_path)
