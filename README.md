# VistaHop Project Page

Static project website for **VistaHop: Benchmarking Long-Horizon Visual DeepSearch**.

## Reviewer dataset

The project page includes a searchable viewer for all **600 VQA tasks** and five
featured cases. Each case contains its image, task query, and reference answer.
The release is stored under `data/vistahop/`:

- `vqa.jsonl`: one task per line for direct download.
- `vqa.json`: browser-ready JSON array used by the explorer.
- `images/`: 600 web-optimized task images.

Serve the directory locally so the browser can load the dataset files:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/> and select **Explore dataset**. The dataset
button and download links resolve to files in this site rather than GitHub.

## Rebuild

From this directory, regenerate the reviewer release from the paper workspace
with:

```bash
python3 scripts/build_dataset_release.py --force
```
