# Tomato Growth-Stage Fusion Classifier

Dual-branch fusion pipeline for classifying tomato plant growth stage
(seeding / developing / flowering / fruiting) from a single photo, combining:

- **Branch 02 — ResNet50**: strips the classifier head, outputs a 2048-dim visual feature vector.
- **Branch 01 — U-Net**: segments the leaf area, reduces it to a 1-dim Leaf Pixel Fraction (LPF).
- **Fusion layer**: concatenates both into a 2049-dim vector fed through a small MLP head.

Three comparison models are trained on the same split: A (ResNet-only), B (LPF-only), C (Fused).

**Live demo:** https://tomato-fusion-demo-628712417253.us-central1.run.app

## Project structure

```
inputs/          Branch checkpoints/loaders/metadata + lpf_full_dataset.csv (authoritative split)
scripts/         Pipeline: 00_refresh_lpf, 01_extract_resnet_features, 02_merge_features,
                 03_train_models, 04_evaluate, model_common (shared MLP head)
checkpoints/     Trained classifier heads (A/B/C) + feature scalers
outputs/         Training histories, run summaries
results/         Confusion matrices, training curves, comparison tables
app/             Streamlit demo UI (streamlit_app.py, inference.py, ui_theme.py)
Dockerfile       CPU-only inference image for Cloud Run deployment
```

## Checkpoints not included in this repo

`inputs/resnet50_tomato_final.pth` (94MB) and `inputs/unet_tomato_final.pth` (31MB) are
excluded to keep the repo lightweight — they're already baked into the deployed Cloud Run
image above. To run the pipeline or app locally, place both files in `inputs/` (matching the
paths referenced in `inputs/resnet_feature_extractor.py` / `inputs/unet_lpf_extractor.py`).

The trained classifier heads in `checkpoints/` (small, a few hundred KB each) *are* included,
so the Streamlit app runs immediately once the two backbone checkpoints above are in place.

## Running locally

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Retraining the pipeline

```
python scripts/00_refresh_lpf.py --dataset-root "<path to dataset>"   # if U-Net checkpoint changed
python scripts/01_extract_resnet_features.py --dataset-root "<path to dataset>"
python scripts/02_merge_features.py
python scripts/03_train_models.py
python scripts/04_evaluate.py
```

## Current test-set results

| Model | Test Accuracy |
|---|---|
| A — ResNet-only | 95.63% |
| B — LPF-only | 68.13% |
| C — Fused | 95.00% |

See `results/tables/comparison_summary.csv` for full per-class precision/recall/F1.
