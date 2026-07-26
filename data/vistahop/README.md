# VistaHop reviewer dataset

This directory contains the website runtime data for all **600 VistaHop VQA
tasks** and **600 web-optimized images**.

## Files

- `tasks.json`: 600 records used by the website explorer.
- `images/`: progressive JPEG derivatives with a maximum dimension of 1920 px.

The reviewer download is published separately as a single self-contained JSONL.
Each line contains the task metadata and Base64-encoded JPEG bytes in
`image_binary`, with `image_encoding` set to `base64`.

Each record contains a stable `uid`, the original `task_id`, relative `image`
path, `task_query`, `reference`, answer aliases, category, scenario, difficulty,
question type, and chain count.

Distribution: **154 L2**, **446 L3**,
**138 single-chain**, and
**462 multi-chain** tasks.

The website images are high-quality derivatives intended for fast reviewer
browsing. Their SHA-256 values and original dimensions are included in the data
records.
