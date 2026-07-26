#!/usr/bin/env python3
"""Build the reviewer-facing VistaHop VQA release for the project website."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps


BATCHES = (
    "_vqa_data",
    "_vqa_data_1",
    "_vqa_data_2",
    "_vqa_data_3",
    "_vqa_data_4",
)
TASK_FILENAMES = {"vqa_single_chain.json", "vqa_multi_chain.json"}
FEATURED_TASK_IDS = {
    "games_01_3_chain_l3",
    "vehicles_06_multi_chain_l3",
    "biology_30_multi_chain_l3",
    "law_02_multi_chain_l3",
    "economy_13_multi_chain_l3",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_category(value: object) -> str:
    category = str(value or "").strip().replace("\\", "/")
    return (category.split("/", 1)[0] or "other").lower()


def infer_scenario(record: dict, task_path: Path) -> str:
    if record.get("scenario"):
        return str(record["scenario"]).strip().lower()
    category = str(record.get("category") or "").strip().replace("\\", "/")
    if "/" in category:
        return category.split("/", 1)[1].lower()
    stem = task_path.parent.name.removesuffix("_vqa")
    return stem.rsplit("_", 1)[0].lower()


def chain_count(record: dict) -> int:
    components = record.get("component_chains")
    if isinstance(components, list) and components:
        return len(components)
    return 1


def task_files(source_root: Path) -> list[Path]:
    paths: list[Path] = []
    for batch in BATCHES:
        batch_root = source_root / batch
        if not batch_root.is_dir():
            raise FileNotFoundError(f"Missing source batch: {batch_root}")
        paths.extend(
            sorted(
                path
                for path in batch_root.rglob("*.json")
                if path.name in TASK_FILENAMES
            )
        )
    return paths


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build(source_root: Path, output_root: Path, force: bool) -> None:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    allowed_site_root = (source_root / "visualdeepsearch.github.io").resolve()
    if output_root != allowed_site_root / "data" / "vistahop":
        raise ValueError(f"Unexpected output directory: {output_root}")

    tasks = task_files(source_root)
    if len(tasks) != 600:
        raise RuntimeError(f"Expected 600 task files, found {len(tasks)}")

    if output_root.exists() and any(output_root.iterdir()) and not force:
        raise FileExistsError(
            f"{output_root} is not empty; rerun with --force to rebuild it"
        )

    images_root = output_root / "images"
    images_root.mkdir(parents=True, exist_ok=True)
    for obsolete_name in ("manifest.json", ".file-organizer-manifest.json"):
        obsolete_path = output_root / obsolete_name
        if obsolete_path.exists():
            obsolete_path.unlink()

    records: list[dict] = []
    operations: list[dict] = []
    web_bytes = 0

    for index, task_path in enumerate(tasks, start=1):
        raw = json.loads(task_path.read_text(encoding="utf-8"))
        for required in ("id", "image", "question", "answer", "difficulty"):
            if required not in raw or raw[required] in ("", None):
                raise ValueError(f"{task_path}: missing required field {required}")

        source_image = (task_path.parent / str(raw["image"])).resolve()
        if not source_image.is_file():
            raise FileNotFoundError(f"{task_path}: missing image {source_image}")
        if source_root not in source_image.parents:
            raise ValueError(f"Image escapes source root: {source_image}")

        uid = f"vistahop-{index:04d}"
        output_image = images_root / f"{uid}.jpg"

        with Image.open(source_image) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            original_width, original_height = image.size
            image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            image.save(
                output_image,
                format="JPEG",
                quality=86,
                optimize=True,
                progressive=True,
                subsampling="4:2:0",
            )
            web_width, web_height = image.size

        source_size = source_image.stat().st_size
        output_size = output_image.stat().st_size
        web_bytes += output_size

        aliases = raw.get("answer_aliases") or []
        if not isinstance(aliases, list):
            aliases = [aliases]

        record = {
            "uid": uid,
            "task_id": str(raw["id"]),
            "image": f"images/{output_image.name}",
            "task_query": str(raw["question"]),
            "reference": str(raw["answer"]),
            "reference_aliases": [str(alias) for alias in aliases],
            "category": normalize_category(raw.get("category")),
            "scenario": infer_scenario(raw, task_path),
            "difficulty": str(raw["difficulty"]).upper(),
            "question_type": str(raw.get("question_type") or "unspecified"),
            "chain_count": chain_count(raw),
            "featured": str(raw["id"]) in FEATURED_TASK_IDS,
            "image_width": web_width,
            "image_height": web_height,
            "original_image_width": original_width,
            "original_image_height": original_height,
            "image_sha256": sha256(output_image),
        }
        records.append(record)
        operations.append(
            {
                "uid": uid,
                "source": str(source_image.relative_to(source_root)),
                "destination": str(output_image.relative_to(allowed_site_root)),
                "source_bytes": source_size,
                "destination_bytes": output_size,
                "source_sha256": sha256(source_image),
                "destination_sha256": record["image_sha256"],
            }
        )

        if index % 50 == 0 or index == len(tasks):
            print(f"Processed {index}/{len(tasks)} images")

    if len({record["uid"] for record in records}) != 600:
        raise RuntimeError("Generated UIDs are not unique")
    if len({record["image"] for record in records}) != 600:
        raise RuntimeError("Generated image paths are not unique")
    if sum(record["featured"] for record in records) != len(FEATURED_TASK_IDS):
        raise RuntimeError("One or more featured task IDs were not found")

    json_path = output_root / "vqa.json"
    jsonl_path = output_root / "vqa.jsonl"
    write_json(json_path, records)
    jsonl_path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    difficulty = Counter(record["difficulty"] for record in records)
    reasoning = Counter(
        "single-chain" if record["chain_count"] == 1 else "multi-chain"
        for record in records
    )
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    write_json(
        source_root / ".vistahop-release-audit.json",
        {
            "operation": "generate_web_dataset_release",
            "generated_at": generated_at,
            "source_root": str(source_root),
            "destination_root": str(output_root),
            "file_count": len(operations),
            "operations": operations,
        },
    )

    readme = f"""# VistaHop reviewer dataset

This directory contains the reviewer-facing release of all **600 VistaHop VQA
tasks** and **600 web-optimized images**.

## Files

- `vqa.jsonl`: one task per line for scripts and streaming readers.
- `vqa.json`: the same 600 records as a JSON array for the website explorer.
- `images/`: progressive JPEG derivatives with a maximum dimension of 1920 px.

Each record contains a stable `uid`, the original `task_id`, relative `image`
path, `task_query`, `reference`, answer aliases, category, scenario, difficulty,
question type, and chain count.

Distribution: **{difficulty["L2"]} L2**, **{difficulty["L3"]} L3**,
**{reasoning["single-chain"]} single-chain**, and
**{reasoning["multi-chain"]} multi-chain** tasks.

The website images are high-quality derivatives intended for fast reviewer
browsing. Their SHA-256 values and original dimensions are included in the data
records.
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")

    print(
        f"Built {len(records)} tasks at {output_root} "
        f"({web_bytes / 1024**2:.1f} MiB of web images)"
    )


def main() -> None:
    script_path = Path(__file__).resolve()
    default_source = script_path.parents[2]
    default_output = script_path.parents[1] / "data" / "vistahop"
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=default_source)
    parser.add_argument("--output-root", type=Path, default=default_output)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    build(args.source_root, args.output_root, args.force)


if __name__ == "__main__":
    main()
