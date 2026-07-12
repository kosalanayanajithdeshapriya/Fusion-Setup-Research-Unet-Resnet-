"""Refresh the lpf column in inputs/lpf_full_dataset.csv using whichever U-Net
checkpoint currently sits at inputs/unet_tomato_final.pth. filename, growth_stage,
and split are left untouched (they stay authoritative). The previous CSV is
backed up once before the first overwrite.

Run this whenever the U-Net checkpoint is replaced, before re-running Tasks 2-4,
so the LPF values training data reflects and what the live UI computes stay
consistent with each other.

Usage:
    python scripts/00_refresh_lpf.py --dataset-root "tomato final dataset"
"""
import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "inputs"))
sys.path.insert(0, str(ROOT / "scripts"))

from unet_lpf_extractor import load_unet, compute_lpf  # noqa: E402
from dataset_index import index_dataset, resolve_path  # noqa: E402

LPF_CSV = ROOT / "inputs" / "lpf_full_dataset.csv"
CHECKPOINT = ROOT / "inputs" / "unet_tomato_final.pth"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True, type=Path)
    args = parser.parse_args()

    df = pd.read_csv(LPF_CSV)
    print(f"loaded {len(df)} rows from {LPF_CSV}")

    backup_path = LPF_CSV.with_name(LPF_CSV.stem + "_backup_before_refresh.csv")
    if not backup_path.exists():
        shutil.copy(LPF_CSV, backup_path)
        print(f"backed up original CSV to {backup_path}")
    else:
        print(f"backup already exists at {backup_path}, not overwriting it")

    print(f"indexing images under {args.dataset_root} ...")
    index = index_dataset(args.dataset_root)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"loading U-Net checkpoint from {CHECKPOINT} on {device} ...")
    model = load_unet(str(CHECKPOINT), device=device)

    new_lpf = []
    missing = []
    for row in tqdm(df.itertuples(), total=len(df), desc="recomputing lpf"):
        path = resolve_path(row.filename, row.split, row.growth_stage, index)
        if path is None:
            missing.append(row.filename)
            new_lpf.append(None)
            continue
        lpf, _ = compute_lpf(model, path)
        new_lpf.append(lpf)

    if missing:
        print(f"ERROR: {len(missing)} filenames not found under {args.dataset_root}:")
        for name in missing[:20]:
            print("  missing:", name)
        raise SystemExit("aborting refresh, no changes written")

    old_lpf = df["lpf"].to_numpy()
    df["lpf"] = new_lpf
    mean_abs_diff = (df["lpf"].to_numpy() - old_lpf)
    print(f"mean abs change in lpf: {abs(mean_abs_diff).mean():.5f}, max: {abs(mean_abs_diff).max():.5f}")

    df.to_csv(LPF_CSV, index=False)
    print(f"refreshed lpf column for {len(df)} rows, saved to {LPF_CSV}")


if __name__ == "__main__":
    main()
