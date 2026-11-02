"""Consolidador e congelador de versão do benchmark (Gold e Silver) com hash SHA256."""
import json
import time
import hashlib
from pathlib import Path
import shutil
from typing import Dict, Any, List


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def run_benchmark_builder(version_tag: str = "v0.3_committee_80") -> Dict[str, Any]:
    print(f"=== [Pipeline] Consolidação e Congelamento do Benchmark ({version_tag}) ===")

    input_file = Path("corpus/validated_approved.jsonl")
    items = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    # Todos os 80 itens aprovados pelos comitês compõem o Benchmark Gold Oficial
    gold_items: List[Dict[str, Any]] = []
    for it in items:
        it_gold = dict(it)
        it_gold["set"] = "gold"
        it_gold["validation_status"] = "auto_only"
        it_gold["validator_id"] = "comite_auditor_3_modelos"
        it_gold["validator_notes"] = f"Aprovado por comitê auditor de 3 modelos menores com rejeição ativa de tautologia: {it.get('auditing_metadata', {}).get('verdict_summary', 'Aprovado')}"
        gold_items.append(it_gold)

    gold_path = Path("corpus/questions_gold.jsonl")
    silver_path = Path("corpus/questions_silver.jsonl")

    with open(gold_path, "w", encoding="utf-8") as f:
        for it in gold_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    silver_items: List[Dict[str, Any]] = []
    for it in gold_items:
        it_silver = dict(it)
        it_silver["set"] = "silver"
        silver_items.append(it_silver)

    with open(silver_path, "w", encoding="utf-8") as f:
        for it in silver_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Pasta de congelamento imutável
    frozen_dir = Path(f"versions/{version_tag}")
    frozen_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(gold_path, frozen_dir / "questions_gold.jsonl")
    shutil.copy(silver_path, frozen_dir / "questions_silver.jsonl")

    gold_cat_counts = {}
    for it in gold_items:
        c = it["primary_type"]
        gold_cat_counts[c] = gold_cat_counts.get(c, 0) + 1

    manifest = {
        "version": version_tag,
        "questions_gold_sha256": compute_sha256(gold_path),
        "questions_silver_sha256": compute_sha256(silver_path),
        "gold_items_count": len(gold_items),
        "silver_items_count": len(silver_items),
        "gold_category_distribution": gold_cat_counts,
        "gold_category_percentages": {cat: f"{(cnt/len(gold_items))*100:.1f}%" for cat, cnt in gold_cat_counts.items()},
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    manifest_file = frozen_dir / "checksums_and_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Benchmark final consolidado e congelado em {frozen_dir}:")
    print(f"  - Gold: {len(gold_items)} itens | SHA256: {manifest['questions_gold_sha256'][:16]}...")
    print(f"  - Silver: {len(silver_items)} itens | SHA256: {manifest['questions_silver_sha256'][:16]}...")
    for cat, cnt in gold_cat_counts.items():
        print(f"    * {cat.upper()}: {cnt} ({manifest['gold_category_percentages'][cat]})")
    return manifest


if __name__ == "__main__":
    run_benchmark_builder()
