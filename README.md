# Tomato Growth Stage Fusion Pipeline

Dual-branch deep learning pipeline that classifies tomato plants into four growth stages — **seeding, developing, flowering, fruiting** — by fusing deep visual features (ResNet50) with an interpretable structural signal (Leaf Pixel Fraction, derived from a U-Net segmentation model).

**Live demo:** https://tomato-fusion-demo-628712417253.us-central1.run.app
*(Cloud Run, scales to zero — first request after idle time may take a few seconds while models load.)*

This repository combines two independently trained models — [Branch 01: U-Net segmentation](#) and [Branch 02: ResNet50 classification](#) — trained in separate projects, referenced here only by their exported, frozen artifacts. See [Project structure](#project-structure) for how this repo relates to the other two.

---

## Overview

```
                     Input Image (224×224×3)
                              │
              ┌───────────────┴───────────────┐
              ▼                                ▼
      ResNet50 (frozen)                 U-Net (frozen)
   2048-dim feature vector          predicted leaf mask
              │                                │
              │                     Leaf Pixel Fraction (LPF)
              │                        = leaf px / total px
              │                                │
              └───────────────┬────────────────┘
                    Concatenate (2049-dim)
                              │
                     Fusion MLP classifier
                              │
                    Predicted growth stage
```

Both branch models remain **frozen**; only the fusion classification head is trained, on top of precomputed features. This is a deliberate design choice — see [Why fusion, and why separate training](#why-fusion-and-why-separate-training) below.

## Results

### Ablation study — test set (n = 160)

| Model | Input | Best Val Acc. | Test Accuracy |
|---|---|---|---|
| A — ResNet-only | 2048-dim CNN features | 100% | **98.75%** |
| B — LPF-only | 1-dim leaf density scalar | 78.5% | 66.25% |
| C — Fused | 2049-dim concatenated | 100% | 98.12% |

- **LPF alone (66.25%)** is far above chance (25% for 4 classes), confirming leaf density is a genuinely informative signal on its own.
- **Fusion (C)** is comparable to, but does not yet exceed, the ResNet-only baseline in aggregate accuracy — the likely cause is dimensionality imbalance at concatenation (a single scalar diluted against 2048 CNN dimensions). An LPF embedding layer is planned to address this; see [Known limitations](#known-limitations--open-work).
- Boundary-specific analysis (developing ↔ flowering, the hardest class pair) is tracked separately from aggregate accuracy, since a real improvement there could exist even without a change in the overall number.

Full confusion matrices, training curves, and per-class precision/recall are in [`results/`](results/).

### Branch results (for reference — trained in their own repos)

| Branch | Metric | Result |
|---|---|---|
| ResNet50 (classification) | Test accuracy | 97.5–98.75% |
| U-Net (segmentation) | Validation Dice / IoU | 0.8134 / 0.7243 |

## Why fusion, and why separate training

Most existing tomato/plant growth-stage systems classify using CNN features alone. This project explicitly tests whether an interpretable, domain-meaningful structural signal — leaf density, derived from segmentation — adds value on top of deep visual features, and reports the result honestly, including the aggregate-level null result alongside a principled explanation.

The two branches are trained **independently** rather than end-to-end, because:
- They need different supervision (ResNet50: image-level growth-stage labels; U-Net: pixel-level segmentation masks, a smaller annotated subset)
- It keeps each branch's contribution isolated and separately evaluable (see ablation above)
- It matches the practical annotation constraints of a self-collected, partially-annotated dataset

## Project structure

```
fusion_layer/
├── inputs/                          copied from each branch's export/ folder
│   ├── resnet50_tomato_final.pth
│   ├── resnet_feature_extractor.py
│   ├── resnet_metadata.json
│   ├── unet_tomato_final.pth
│   ├── unet_lpf_extractor.py
│   ├── unet_metadata.json
│   └── lpf_full_dataset.csv         authoritative train/valid/test split for ALL fusion work
├── scripts/
│   ├── 01_extract_resnet_features.py
│   ├── 02_merge_features.py
│   ├── 03_train_fusion.py           trains Models A / B / C
│   └── 04_evaluate.py               ablation evaluation + comparison tables
├── results/
│   ├── tables/                      comparison_summary, developing_flowering_boundary
│   └── plots/                       confusion_matrices.png, training_curves.png
├── app/                             Streamlit demo UI
├── Dockerfile                       CPU-only PyTorch build for Cloud Run
├── .dockerignore / .gcloudignore    excludes the ~5.7GB training dataset from the image
└── README.md
```

**Note:** `inputs/` files are copied from the ResNet50 and U-Net projects' own `export/` folders after they are trained and exported there. This repo has no dependency on either project's training code — only on their standalone exported artifacts.

## Running the pipeline

```bash
pip install -r requirements.txt

python scripts/01_extract_resnet_features.py   # 2048-dim features for every image
python scripts/02_merge_features.py            # join with lpf_full_dataset.csv on filename
python scripts/03_train_fusion.py              # trains Models A, B, C
python scripts/04_evaluate.py                  # test-set evaluation + comparison tables
```

All scripts use the `split` column in `inputs/lpf_full_dataset.csv` as the single source of truth for train/valid/test assignment, to keep results consistent with the branch projects and avoid re-splitting/leakage.

## Predicting on a new image

Since both branches predict rather than require ground truth at inference time, this works on **any new, unannotated tomato photo**:

```python
from predict import predict_growth_stage

stage, confidence = predict_growth_stage("path/to/new_image.jpg")
print(f"{stage} ({confidence*100:.1f}% confidence)")
```

## Live demo

A Streamlit UI wrapping the full pipeline is deployed on Google Cloud Run:

**https://tomato-fusion-demo-628712417253.us-central1.run.app**

| | |
|---|---|
| Hosting | Cloud Run (`tomato-fusion-demo`, `us-central1`), 2 vCPU / 2 GiB RAM |
| Image | CPU-only PyTorch build, ~128 MB (training dataset excluded via `.dockerignore`/`.gcloudignore`) |
| Registry | Artifact Registry — `tomato-fusion` repo, `us-central1` |
| Scaling | Scales to zero when idle; first request after idle time has a cold-start delay (models loading) |
| Cost | ~free under Cloud Run's free tier (2M requests/month) for demo-level traffic; a few cents/month for image storage |

**Redeploy after retraining or a UI change:**
```bash
cd d:\Reasearch\fusion_layer
gcloud builds submit --tag us-central1-docker.pkg.dev/ytapi-496016/tomato-fusion/app:latest --project=ytapi-496016
gcloud run deploy tomato-fusion-demo --image us-central1-docker.pkg.dev/ytapi-496016/tomato-fusion/app:latest --project=ytapi-496016 --region=us-central1
```

**Tear down (stop all cost):**
```bash
gcloud run services delete tomato-fusion-demo --project=ytapi-496016 --region=us-central1
```

## Known limitations / open work

- **Fusion does not yet exceed the ResNet-only baseline in aggregate accuracy.** An LPF embedding layer (`Dense(16, ReLU)` before concatenation) is planned to address dimensionality imbalance; results will be re-run and compared on the developing/flowering boundary specifically, not only aggregate accuracy.
- **100% validation accuracy on Models A and C** is flagged as a possible small/easy-validation-set artifact rather than confirmed model perfection; worth checking validation set size and considering k-fold cross-validation for more robust model selection.
- **Data leakage audit in progress.** An early ResNet50 training notebook was found to use an internal random split rather than the folder-based split; a perceptual-hash near-duplicate scan across train/valid/test is underway. This fusion project already enforces the strict folder-based split throughout, so it is not affected going forward, but the upstream ResNet50 number carries this caveat — see the ResNet50 branch's own README/metadata for details.
- **U-Net segmentation quality (Dice 0.81)** has room to improve; a pretrained encoder backbone is planned for a future branch iteration, with the fusion ablation intended to be re-run against it to see whether stronger segmentation improves the fusion result.
- **Backbone comparison** (ResNet18/34/50/101) is in progress in the ResNet50 branch project to confirm ResNet50 is the right accuracy/efficiency tradeoff for this dataset size.

## Part of

This repository is the fusion stage of the [Tomato Plant Growth Stage Monitoring System](https://tomatoresearch.vercel.app/) research project, combining the ResNet50 classification branch and the U-Net segmentation branch.

## License

Released under the MIT License.
