"""The PhishLens model: name features and a letter-pattern score, combined by LightGBM, explained with SHAP.

Saved as plain files, so loading a model never runs code: LightGBM's text format, a NumPy array, and JSON.
"""
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from .features import COLUMNS, NUMERIC, name_features
from .pattern import NamePattern

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
SHARED_HOSTING_AS = "com"


class PhishLens:
    def __init__(self, booster, pattern, suffixes, metadata=None):
        self.booster = booster
        self.pattern = pattern
        self.suffixes = list(suffixes)  # suffixes the model knows; any other becomes "other"
        self.metadata = metadata or {}

    def frame(self, names, suffixes, shared_hosting=None):
        """Model inputs for registered names and their suffixes."""
        suffixes = list(suffixes)
        if shared_hosting is not None:
            # A hosting platform says nothing about the site on it, and the model never saw one: judge the site's
            # name as if it ended in the commonest suffix, so the platform neither raises nor lowers the risk
            suffixes = [SHARED_HOSTING_AS if shared else s for s, shared in zip(suffixes, shared_hosting)]
        rows = pd.DataFrame([name_features(n, s) for n, s in zip(names, suffixes)], columns=NUMERIC)
        known = [s if s in self.suffixes else "other" for s in suffixes]
        rows["suffix"] = pd.Categorical(known, categories=self.suffixes + ["other"])
        rows["name_pattern"] = self.pattern.score(names)
        return rows[COLUMNS]

    def score(self, frame):
        """Probability that each domain is a phishing domain."""
        return self.booster.predict(frame)

    def contributions(self, frame):
        """SHAP values from LightGBM's exact TreeSHAP, in log-odds. The last column is the base value."""
        return self.booster.predict(frame, pred_contrib=True)

    def save(self, directory=MODEL_DIR):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.booster.save_model(directory / "phishlens.lgb.txt")
        np.savez_compressed(directory / "name_pattern.npz", coef=self.pattern.coef.astype(np.float32),
                            intercept=np.array([self.pattern.intercept]))
        meta = dict(self.metadata, suffixes=self.suffixes, columns=COLUMNS)
        (directory / "phishlens.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, directory=MODEL_DIR):
        directory = Path(directory)
        meta = json.loads((directory / "phishlens.json").read_text(encoding="utf-8"))
        if meta.get("columns") != COLUMNS:
            raise ValueError("this model was saved with different features; retrain it with train.py")
        with np.load(directory / "name_pattern.npz", allow_pickle=False) as arrays:
            pattern = NamePattern(arrays["coef"], arrays["intercept"][0])
        booster = lgb.Booster(model_file=str(directory / "phishlens.lgb.txt"))
        return cls(booster, pattern, meta["suffixes"], meta)
