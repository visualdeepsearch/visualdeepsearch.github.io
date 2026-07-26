# VistaHop reviewer dataset

This directory contains the reviewer-facing release of all **600 VistaHop VQA
tasks** and **600 web-optimized images**.

## Files

- `vqa.jsonl`: one task per line for scripts and streaming readers.
- `vqa.json`: the same 600 records as a JSON array for the website explorer.
- `images/`: progressive JPEG derivatives with a maximum dimension of 1920 px.

Each record contains a stable `uid`, the original `task_id`, relative `image`
path, `task_query`, `reference`, answer aliases, category, scenario, difficulty,
question type, and chain count.

Distribution: **154 L2**, **446 L3**,
**138 single-chain**, and
**462 multi-chain** tasks.

The website images are high-quality derivatives intended for fast reviewer
browsing. Their SHA-256 values and original dimensions are included in the data
records.
