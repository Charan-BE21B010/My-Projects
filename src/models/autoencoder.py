from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class TabularAutoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list[int] | None = None):
        super().__init__()
        hidden_dims = hidden_dims or [64, 32, 16]
        dims = [input_dim] + hidden_dims
        enc = []
        for i in range(len(dims) - 1):
            enc += [nn.Linear(dims[i], dims[i + 1]), nn.ReLU()]
        self.encoder = nn.Sequential(*enc)

        dec_dims = list(reversed(dims))
        dec = []
        for i in range(len(dec_dims) - 1):
            dec.append(nn.Linear(dec_dims[i], dec_dims[i + 1]))
            if i < len(dec_dims) - 2:
                dec.append(nn.ReLU())
        self.decoder = nn.Sequential(*dec)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


class AutoencoderFraudModel:
    def __init__(
        self,
        hidden_dims: list[int] | None = None,
        epochs: int = 8,
        batch_size: int = 2048,
        lr: float = 1e-3,
        threshold_percentile: float = 95.0,
        device: str | None = None,
    ):
        self.hidden_dims = hidden_dims or [64, 32, 16]
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.threshold_percentile = threshold_percentile
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model: TabularAutoencoder | None = None
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None
        self.threshold_: float = 0.0

    def _scale(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mean_ = X.mean(axis=0)
            self.std_ = X.std(axis=0) + 1e-6
        assert self.mean_ is not None and self.std_ is not None
        return (X - self.mean_) / self.std_

    def fit(self, X: np.ndarray, y: np.ndarray) -> "AutoencoderFraudModel":
        # Train primarily on normal transactions
        X_norm = X[y == 0]
        if len(X_norm) < 100:
            X_norm = X
        Xs = self._scale(X_norm, fit=True)
        self.model = TabularAutoencoder(Xs.shape[1], self.hidden_dims).to(self.device)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        loss_fn = nn.MSELoss()

        loader = DataLoader(
            TensorDataset(torch.tensor(Xs, dtype=torch.float32)),
            batch_size=self.batch_size,
            shuffle=True,
        )

        self.model.train()
        for _ in range(self.epochs):
            for (batch,) in loader:
                batch = batch.to(self.device)
                opt.zero_grad()
                recon = self.model(batch)
                loss = loss_fn(recon, batch)
                loss.backward()
                opt.step()

        # Threshold from reconstruction error on normal data
        errors = self.reconstruction_error(X_norm)
        self.threshold_ = float(np.percentile(errors, self.threshold_percentile))
        return self

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        assert self.model is not None
        Xs = self._scale(X, fit=False)
        self.model.eval()
        with torch.no_grad():
            t = torch.tensor(Xs, dtype=torch.float32, device=self.device)
            recon = self.model(t).cpu().numpy()
        return np.mean((Xs - recon) ** 2, axis=1)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        errors = self.reconstruction_error(X)
        # Map error relative to threshold into [0, 1]
        scores = errors / (self.threshold_ + 1e-6)
        return np.clip(scores / (1.0 + scores), 0.0, 1.0)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state_dict": self.model.state_dict() if self.model else None,
            "hidden_dims": self.hidden_dims,
            "mean_": self.mean_,
            "std_": self.std_,
            "threshold_": self.threshold_,
            "input_dim": None if self.mean_ is None else int(len(self.mean_)),
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "lr": self.lr,
            "threshold_percentile": self.threshold_percentile,
        }
        torch.save(payload, path)

    @classmethod
    def load(cls, path: str | Path, device: str | None = None) -> "AutoencoderFraudModel":
        payload = torch.load(path, map_location="cpu", weights_only=False)
        inst = cls(
            hidden_dims=payload["hidden_dims"],
            epochs=payload["epochs"],
            batch_size=payload["batch_size"],
            lr=payload["lr"],
            threshold_percentile=payload["threshold_percentile"],
            device=device,
        )
        inst.mean_ = payload["mean_"]
        inst.std_ = payload["std_"]
        inst.threshold_ = payload["threshold_"]
        inst.model = TabularAutoencoder(payload["input_dim"], payload["hidden_dims"]).to(inst.device)
        inst.model.load_state_dict(payload["state_dict"])
        inst.model.eval()
        return inst
