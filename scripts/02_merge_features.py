"""Task 2: inner-join resnet_features_full with lpf_full_dataset.csv on filename.

Confirms growth_stage and split agree between the two sources before saving
the combined table; aborts if any mismatch is found.

Usage:
    python scripts/02_merge_features.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FEATURES_NPZ = ROOT / "outputs" / "resnet_features_full.npz"
LPF_CSV = ROOT / "inputs" / "lpf_full_dataset.csv"
OUTPUT = ROOT / "outputs" / "combined_features.npz"


def main():
    feat_data = np.load(FEATURES_NPZ, allow_pickle=True)
    feat_df = pd.DataFrame({
        "filename": feat_data["filename"],
        "growth_stage_resnet": feat_data["growth_stage"],
        "split_resnet": feat_data["split"],
    })
    features = feat_data["resnet_features"]  # (N, 2048), row-aligned with feat_df

    lpf_df = pd.read_csv(LPF_CSV).rename(
        columns={"growth_stage": "growth_stage_lpf", "split": "split_lpf"}
    )

    merged = feat_df.merge(lpf_df, on="filename", how="inner")

    if len(merged) != len(feat_df) or len(merged) != len(lpf_df):
        print(f"WARNING: inner join reduced row count. resnet={len(feat_df)}, "
              f"lpf={len(lpf_df)}, merged={len(merged)}")

    stage_mismatch = merged[merged["growth_stage_resnet"] != merged["growth_stage_lpf"]]
    split_mismatch = merged[merged["split_resnet"] != merged["split_lpf"]]

    if len(stage_mismatch) or len(split_mismatch):
        print(f"MISMATCH: {len(stage_mismatch)} growth_stage disagreements, "
              f"{len(split_mismatch)} split disagreements between sources.")
        if len(stage_mismatch):
            print(stage_mismatch[["filename", "growth_stage_resnet", "growth_stage_lpf"]].head(20).to_string())
        if len(split_mismatch):
            print(split_mismatch[["filename", "split_resnet", "split_lpf"]].head(20).to_string())
        raise SystemExit(
            "Aborting: resolve growth_stage/split mismatches between resnet_features_full "
            "and lpf_full_dataset.csv before training."
        )

    print(f"OK: all {len(merged)} rows agree on growth_stage and split across both sources.")

    filename_to_row = {fn: i for i, fn in enumerate(feat_df["filename"])}
    feat_idx = merged["filename"].map(filename_to_row).to_numpy()
    aligned_features = features[feat_idx]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUTPUT,
        filename=merged["filename"].to_numpy(),
        growth_stage=merged["growth_stage_lpf"].to_numpy(),
        split=merged["split_lpf"].to_numpy(),
        resnet_features=aligned_features,
        lpf=merged["lpf"].to_numpy(),
    )
    print(f"saved combined table ({len(merged)} rows, 2048 resnet dims + 1 lpf dim) to {OUTPUT}")


if __name__ == "__main__":
    main()
