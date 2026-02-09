from __future__ import annotations
# ruff: noqa: E402

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import engine, get_db
from equipment import upsert_equipment_from_json
from models_db import Base


def _iter_json_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for json_file in sorted(path.glob("*.json")):
        if json_file.is_file():
            yield json_file


def _load_items(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise ValueError(
        f"{path} must contain a JSON list or an object with an 'items' list."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed equipment rows from JSON files."
    )
    parser.add_argument(
        "--path",
        default=str(BACKEND_DIR / "data" / "items"),
        help="Path to a JSON file or directory containing JSON files.",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Path does not exist: {path}")
        return 1

    files = list(_iter_json_files(path))
    if not files:
        print(f"No JSON files found in: {path}")
        return 1

    Base.metadata.create_all(bind=engine)
    total_inserted = 0
    total_updated = 0
    total_skipped = 0
    total_items = 0

    with get_db() as db:
        try:
            for json_file in files:
                items = _load_items(json_file)
                result = upsert_equipment_from_json(db, items)
                total_inserted += result["inserted"]
                total_updated += result["updated"]
                total_skipped += result["skipped"]
                total_items += result["total"]
                print(
                    f"{json_file.name}: inserted={result['inserted']} "
                    f"updated={result['updated']} skipped={result['skipped']} "
                    f"total={result['total']}"
                )
        except ValueError as exc:
            print(f"Validation error while seeding equipment JSON: {exc}")
            return 1

    print(
        f"Done. inserted={total_inserted} updated={total_updated} "
        f"skipped={total_skipped} total={total_items}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
