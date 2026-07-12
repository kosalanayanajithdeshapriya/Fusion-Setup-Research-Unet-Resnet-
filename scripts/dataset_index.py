"""Shared filename-based dataset resolution, used by any script that needs to
locate an actual image file on disk from a (filename, split, growth_stage) row
without assuming a fixed folder layout.
"""
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def index_dataset(dataset_root):
    """Map filename -> list of full paths found anywhere under dataset_root."""
    index = {}
    for p in dataset_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            index.setdefault(p.name, []).append(p)
    return index


def resolve_path(filename, split, growth_stage, index):
    candidates = index.get(filename)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    split_matches = [p for p in candidates if split in p.parts]
    pool = split_matches or candidates
    stage_matches = [p for p in pool if growth_stage in p.parts]
    if len(stage_matches) == 1:
        return stage_matches[0]
    if len(split_matches) == 1:
        return split_matches[0]
    return pool[0]
