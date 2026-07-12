"""Task 1: extract ResNet50 (2048-dim) features for every image in lpf_full_dataset.csv.

Does not assume a fixed class/split subfolder layout on disk. Instead it indexes
the whole dataset root once (filename -> path), then resolves each CSV row's
filename against that index, disambiguating with the split/growth_stage columns
if a filename happens to appear more than once.

Usage:
    python scripts/01_extract_resnet_features.py --dataset-root "D:/path/to/dataset"
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "inputs"))
sys.path.insert(0, str(ROOT / "scripts"))

from resnet_feature_extractor import load_resnet_feature_extractor, PREPROCESS  # noqa: E402
from dataset_index import index_dataset, resolve_path  # noqa: E402

LPF_CSV = ROOT / "inputs" / "lpf_full_dataset.csv"
CHECKPOINT = ROOT / "inputs" / "resnet50_tomato_final.pth"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output", default=ROOT / "outputs" / "resnet_features_full.npz", type=Path)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    df = pd.read_csv(LPF_CSV)
    print(f"loaded {len(df)} rows from {LPF_CSV}")

    print(f"indexing images under {args.dataset_root} ...")
    index = index_dataset(args.dataset_root)
    n_files = sum(len(v) for v in index.values())
    print(f"found {n_files} image files on disk ({len(index)} unique filenames)")

    resolved_paths = []
    missing = []
    for row in df.itertuples():
        path = resolve_path(row.filename, row.split, row.growth_stage, index)
        resolved_paths.append(path)
        if path is None:
            missing.append(row.filename)

    if missing:
        print(f"ERROR: {len(missing)} of {len(df)} filenames from the CSV were not found "
              f"under {args.dataset_root}")
        for name in missing[:20]:
            print("  missing:", name)
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"loading ResNet50 feature extractor on {device} ...")
    model = load_resnet_feature_extractor(str(CHECKPOINT), device=device)

    features = np.zeros((len(df), 2048), dtype=np.float32)
    with torch.no_grad():
        for start in tqdm(range(0, len(resolved_paths), args.batch_size), desc="extracting features"):
            end = min(start + args.batch_size, len(resolved_paths))
            batch_imgs = [PREPROCESS(Image.open(resolved_paths[i]).convert("RGB")) for i in range(start, end)]
            batch = torch.stack(batch_imgs).to(device)
            out = model(batch).cpu().numpy()
            features[start:end] = out

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        filename=df["filename"].to_numpy(),
        growth_stage=df["growth_stage"].to_numpy(),
        split=df["split"].to_numpy(),
        resnet_features=features,
    )
    print(f"saved {features.shape} feature matrix to {args.output}")


if __name__ == "__main__":
    main()
