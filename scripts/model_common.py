"""Shared model definition used by both 03_train_models.py and 04_evaluate.py."""
import random

import numpy as np
import torch
import torch.nn as nn


class MLPHead(nn.Module):
    def __init__(self, in_dim, hidden_dim, num_classes, dropout=0.0):
        super().__init__()
        layers = [nn.Linear(in_dim, hidden_dim), nn.ReLU()]
        if dropout > 0:
            layers.append(nn.Dropout(dropout))
        layers.append(nn.Linear(hidden_dim, num_classes))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)  # logits; CrossEntropyLoss applies log-softmax internally


MODEL_CONFIGS = {
    "A_resnet_only": dict(in_dim=2048, hidden_dim=128, dropout=0.3, display_name="Model A (ResNet-only)"),
    "B_lpf_only": dict(in_dim=1, hidden_dim=16, dropout=0.0, display_name="Model B (LPF-only)"),
    "C_fused": dict(in_dim=2049, hidden_dim=128, dropout=0.3, display_name="Model C (Fused)"),
}


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)
