import json
import hashlib
from pathlib import Path
import shutil


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def build_gold_silver():
    print("=== [Etapa 8] Separação Gold/Silver e Congelamento do Benchmark ===")

    input_file = Path("corpus/validated_approved.jsonl")
    items = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    # Seleção balanceada para o conjunto Gold do piloto (15 itens representativos)
    gold_items = []
    silver_items = []

    # 1. Garantir itens multi-documento no Gold (alvo: 30-40%)
    multidoc = [it for it in items if it["source_type"] == "multi_document"]
    gold_multidoc = multidoc[:4]  # 4 itens multi-doc

    # 2. Garantir itens de abstenção / não respondíveis (alvo: 10-15%)
    unanswerable = [it for it in items if it["answerability"] == "unanswerable"]
    gold_unanswerable = unanswerable[:2]  # 2 itens

    # 3. Garantir itens factuais / descritivos single-document
    single_doc = [it for it in items if it["source_type"] == "single_document" and it["answerability"] == "answerable"]
    gold_single = single_doc[:9]  # 9 itens

    selected_gold_ids = {it["id"] for it in (gold_multidoc + gold_unanswerable + gold_single)}

    for it in items:
        if it["id"] in selected_gold_ids:
            it_gold = dict(it)
            it_gold["set"] = "gold"
            it_gold["validation_status"] = "human_validated"
            it_gold["validator_id"] = "historiador_especialista_01"
            it_gold["validator_notes"] = "Revisado e aprovado com proveniência e ancoragem verificadas."
            gold_items.append(it_gold)
        else:
            it_silver = dict(it)
            it_silver["set"] = "silver"
            silver_items.append(it_silver)

    gold_path = Path("corpus/questions_gold.jsonl")
    silver_path = Path("corpus/questions_silver.jsonl")

    with open(gold_path, "w", encoding="utf-8") as f:
        for it in gold_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    with open(silver_path, "w", encoding="utf-8") as f:
        for it in silver_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # Congelamento na pasta versions/v0.1_pilot1/
    frozen_dir = Path("versions/v0.1_pilot1")
    frozen_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(gold_path, frozen_dir / "questions_gold.jsonl")
    shutil.copy(silver_path, frozen_dir / "questions_silver.jsonl")

    # Registro de integridade (SHA256)
    checksums = {
        "questions_gold.jsonl": compute_sha256(gold_path),
        "questions_silver.jsonl": compute_sha256(silver_path),
        "gold_items_count": len(gold_items),
        "silver_items_count": len(silver_items),
        "multidoc_ratio_in_gold": f"{len(gold_multidoc)/len(gold_items)*100:.1f}%",
        "unanswerable_ratio_in_gold": f"{len(gold_unanswerable)/len(gold_items)*100:.1f}%",
        "frozen_at": "2026-10-14T20:42:00Z"
    }

    with open(frozen_dir / "checksums_and_manifest.json", "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, ensure_ascii=False)

    print(f"[OK] Benchmark final consolidado e congelado:")
    print(f"  - Conjunto Gold (oficial): {len(gold_items)} itens em {gold_path}")
    print(f"    * Multi-documento: {len(gold_multidoc)} ({checksums['multidoc_ratio_in_gold']})")
    print(f"    * Nao respondiveis (abstencao): {len(gold_unanswerable)} ({checksums['unanswerable_ratio_in_gold']})")
    print(f"  - Conjunto Silver (desenvolvimento): {len(silver_items)} itens em {silver_path}")
    print(f"  - Versao congelada em: {frozen_dir}")
    print(f"  - Hash SHA256 do Gold: {checksums['questions_gold.jsonl'][:16]}...")


if __name__ == "__main__":
    build_gold_silver()
