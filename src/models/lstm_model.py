from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class LSTMClassifier(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 64, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1 if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        return self.head(last).squeeze(-1)


class LSTMFraudModel:
    def __init__(
        self,
        hidden_size: int = 64,
        num_layers: int = 2,
        epochs: int = 6,
        batch_size: int = 1024,
        lr: float = 1e-3,
        device: str | None = None,
    ):
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model: LSTMClassifier | None = None
        self.seq_mean: float = 0.0
        self.seq_std: float = 1.0

    def fit(self, sequences: np.ndarray, y: np.ndarray) -> "LSTMFraudModel":
        # sequences: [N, T]
        self.seq_mean = float(sequences.mean())
        self.seq_std = float(sequences.std() + 1e-6)
        Xs = ((sequences - self.seq_mean) / self.seq_std).astype(np.float32)
        X_t = torch.tensor(Xs[..., None], dtype=torch.float32)
        y_t = torch.tensor(y.astype(np.float32))

        self.model = LSTMClassifier(1, self.hidden_size, self.num_layers).to(self.device)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)

        pos = max(float(y.sum()), 1.0)
        neg = max(float(len(y) - y.sum()), 1.0)
        pos_weight = torch.tensor([neg / pos], device=self.device)
        loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

        loader = DataLoader(TensorDataset(X_t, y_t), batch_size=self.batch_size, shuffle=True)
        self.model.train()
        for _ in range(self.epochs):
            for xb, yb in loader:
                xb = xb.to(self.device)
                yb = yb.to(self.device)
                opt.zero_grad()
                logits = self.model(xb)
                loss = loss_fn(logits, yb)
                loss.backward()
                opt.step()
        return self

    def predict_proba(self, sequences: np.ndarray) -> np.ndarray:
        assert self.model is not None
        Xs = ((sequences - self.seq_mean) / self.seq_std).astype(np.float32)
        self.model.eval()
        probs = []
        with torch.no_grad():
            for i in range(0, len(Xs), self.batch_size):
                batch = torch.tensor(Xs[i : i + self.batch_size, :, None], dtype=torch.float32, device=self.device)
                logits = self.model(batch)
                probs.append(torch.sigmoid(logits).cpu().numpy())
        return np.concatenate(probs, axis=0)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict() if self.model else None,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers,
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "lr": self.lr,
                "seq_mean": self.seq_mean,
                "seq_std": self.seq_std,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path, device: str | None = None) -> "LSTMFraudModel":
        payload = torch.load(path, map_location="cpu", weights_only=False)
        inst = cls(
            hidden_size=payload["hidden_size"],
            num_layers=payload["num_layers"],
            epochs=payload["epochs"],
            batch_size=payload["batch_size"],
            lr=payload["lr"],
            device=device,
        )
        inst.seq_mean = payload["seq_mean"]
        inst.seq_std = payload["seq_std"]
        inst.model = LSTMClassifier(1, inst.hidden_size, inst.num_layers).to(inst.device)
        inst.model.load_state_dict(payload["state_dict"])
        inst.model.eval()
        return inst
