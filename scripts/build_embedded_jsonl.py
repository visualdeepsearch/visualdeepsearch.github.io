#!/usr/bin/env python3
"""Build a self-contained VistaHop JSONL with Base64-encoded image bytes."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path


EXPECTED_RECORDS = 600


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build(dataset_root: Path, output_path: Path) -> None:
    dataset_root = dataset_root.resolve()
    records_path = dataset_root / "vqa.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))

    if not isinstance(records, list) or len(records) != EXPECTED_RECORDS:
        raise RuntimeError(
            f"Expected {EXPECTED_RECORDS} records in {records_path}, "
            f"found {len(records) if isinstance(records, list) else 'non-list data'}"
        )

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")

    seen_uids: set[str] = set()
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
            for index, source_record in enumerate(records, start=1):
                record = dict(source_record)
                uid = str(record.get("uid") or "")
                if not uid or uid in seen_uids:
                    raise RuntimeError(f"Record {index} has a missing or duplicate uid")
                seen_uids.add(uid)

                relative_image = Path(str(record.pop("image", "")))
                image_path = (dataset_root / relative_image).resolve()
                if dataset_root not in image_path.parents or not image_path.is_file():
                    raise FileNotFoundError(
                        f"{uid}: missing or invalid image path {relative_image}"
                    )

                image_bytes = image_path.read_bytes()
                expected_hash = str(record.get("image_sha256") or "")
                actual_hash = sha256_bytes(image_bytes)
                if expected_hash and expected_hash != actual_hash:
                    raise RuntimeError(
                        f"{uid}: image SHA-256 mismatch "
                        f"({expected_hash} != {actual_hash})"
                    )

                record.update(
                    {
                        "image_filename": image_path.name,
                        "image_mime_type": "image/jpeg",
                        "image_encoding": "base64",
                        "image_binary": base64.b64encode(image_bytes).decode("ascii"),
                    }
                )
                handle.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                )
                handle.write("\n")

                if index % 50 == 0 or index == len(records):
                    print(f"Embedded {index}/{len(records)} images", flush=True)

        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    print(
        f"Built {len(records)} records at {output_path} "
        f"({output_path.stat().st_size / 1024**2:.1f} MiB)"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data/vistahop"),
        help="Directory containing vqa.json and images/",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/vistahop-600-vqa-with-images.jsonl"),
        help="Destination JSONL path",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build(arguments.dataset_root, arguments.output)
