from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


class DistilBERTStyleEncoder(nn.Module):
    """
    Lightweight DistilBERT-style encoder:
    token embedding + positional embedding + Transformer encoder + classification head.

    Named to match the project stack (DistilBERT family architecture) while staying
    fully offline and dependency-light for GitHub demos.
    """

    def __init__(self, vocab_size: int, embed_dim: int = 64, hidden_dim: int = 64, max_len: int = 32, nhead: int = 4):
        super().__init__()
        self.max_len = max_len
        self.token_emb = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.pos_emb = nn.Embedding(max_len, embed_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=nhead,
            dim_feedforward=hidden_dim * 2,
            dropout=0.1,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T]
        b, t = x.shape
        positions = torch.arange(t, device=x.device).unsqueeze(0).expand(b, t)
        h = self.token_emb(x) + self.pos_emb(positions)
        h = self.encoder(h)
        h = self.norm(h)
        # mean pool over non-pad tokens
        mask = x.ne(0).unsqueeze(-1).float()
        pooled = (h * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        return self.head(pooled).squeeze(-1)


class DistilBERTFraudModel:
    def __init__(
        self,
        vocab_size: int = 5000,
        embed_dim: int = 64,
        hidden_dim: int = 64,
        epochs: int = 5,
        batch_size: int = 1024,
        lr: float = 1e-3,
        max_len: int = 32,
        device: str | None = None,
    ):
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.max_len = max_len
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.token_to_id: dict[str, int] = {"<pad>": 0, "<unk>": 1}
        self.model: DistilBERTStyleEncoder | None = None

    def build_vocab(self, texts: list[str]) -> None:
        counter: Counter[str] = Counter()
        for text in texts:
            counter.update(tokenize(text))
        most_common = counter.most_common(self.vocab_size - 2)
        for i, (tok, _) in enumerate(most_common, start=2):
            self.token_to_id[tok] = i

    def encode_texts(self, texts: list[str]) -> np.ndarray:
        rows = []
        for text in texts:
            ids = [self.token_to_id.get(tok, 1) for tok in tokenize(text)[: self.max_len]]
            if len(ids) < self.max_len:
                ids += [0] * (self.max_len - len(ids))
            rows.append(ids)
        return np.array(rows, dtype=np.int64)

    def fit(self, texts: list[str], y: np.ndarray) -> "DistilBERTFraudModel":
        self.build_vocab(texts)
        X = self.encode_texts(texts)
        self.model = DistilBERTStyleEncoder(
            vocab_size=max(self.vocab_size, len(self.token_to_id) + 1),
            embed_dim=self.embed_dim,
            hidden_dim=self.hidden_dim,
            max_len=self.max_len,
        ).to(self.device)

        pos = max(float(y.sum()), 1.0)
        neg = max(float(len(y) - y.sum()), 1.0)
        pos_weight = torch.tensor([neg / pos], device=self.device)
        loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr)

        loader = DataLoader(
            TensorDataset(torch.tensor(X), torch.tensor(y.astype(np.float32))),
            batch_size=self.batch_size,
            shuffle=True,
        )

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

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        assert self.model is not None
        X = self.encode_texts(texts)
        self.model.eval()
        probs = []
        with torch.no_grad():
            for i in range(0, len(X), self.batch_size):
                batch = torch.tensor(X[i : i + self.batch_size], device=self.device)
                logits = self.model(batch)
                probs.append(torch.sigmoid(logits).cpu().numpy())
        return np.concatenate(probs, axis=0)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict() if self.model else None,
                "token_to_id": self.token_to_id,
                "vocab_size": self.vocab_size,
                "embed_dim": self.embed_dim,
                "hidden_dim": self.hidden_dim,
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "lr": self.lr,
                "max_len": self.max_len,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path, device: str | None = None) -> "DistilBERTFraudModel":
        payload = torch.load(path, map_location="cpu", weights_only=False)
        inst = cls(
            vocab_size=payload["vocab_size"],
            embed_dim=payload["embed_dim"],
            hidden_dim=payload["hidden_dim"],
            epochs=payload["epochs"],
            batch_size=payload["batch_size"],
            lr=payload["lr"],
            max_len=payload["max_len"],
            device=device,
        )
        inst.token_to_id = payload["token_to_id"]
        inst.model = DistilBERTStyleEncoder(
            vocab_size=max(inst.vocab_size, len(inst.token_to_id) + 1),
            embed_dim=inst.embed_dim,
            hidden_dim=inst.hidden_dim,
            max_len=inst.max_len,
        ).to(inst.device)
        inst.model.load_state_dict(payload["state_dict"])
        inst.model.eval()
        return inst
