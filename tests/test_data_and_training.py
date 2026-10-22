import json
import random

import pandas as pd

import predict
import train
from phishlens.data import load_urls, to_domains


def write_dataset(path, n=600, seed=0):
    """A small file in PhiUSIIL's format: label 1 is legitimate, and legitimate URLs are bare www home pages."""
    rnd = random.Random(seed)
    words = ["garden", "travel", "music", "book", "river", "stone", "cloud", "metro", "pixel", "harbor", "maple"]
    rows = []
    for i in range(n):
        name = f"{rnd.choice(words)}{rnd.choice(words)}{i}"
        rows.append((f"https://www.{name}.com", 1))
        bad = f"secure-{rnd.choice(['login', 'verify', 'update'])}-{rnd.randrange(10**6)}"
        rows.append((f"http://{bad}.{rnd.choice(['xyz', 'top', 'info'])}/signin", 0))
    rows += [("https://shop.web.app/", 0), ("http://10.0.0.1/x", 0),          # shared hosting and an IP: left out
             ("https://www.both.com", 1), ("https://both.com/phish", 0)]     # both labels: left out
    frame = pd.DataFrame(rows, columns=["URL", "label"])
    frame.insert(0, "FILENAME", "x")
    frame.to_csv(path, index=False)


def test_domains_are_cleaned(tmp_path):
    write_dataset(tmp_path / "d.csv", n=10)
    urls = load_urls(tmp_path / "d.csv")
    assert set(urls["phishing"]) == {0, 1}
    domains, stats = to_domains(urls)
    assert stats["shared_hosting_urls"] == 1 and stats["ip_urls"] == 1 and stats["mixed_label_domains"] == 1
    assert len(domains) == 20 and domains[["name", "suffix"]].duplicated().sum() == 0


def test_training_end_to_end(tmp_path, capsys):
    write_dataset(tmp_path / "d.csv")
    train.main(["--data", str(tmp_path / "d.csv"), "--out", str(tmp_path / "model")])
    metrics = json.loads((tmp_path / "model" / "metrics.json").read_text())
    assert metrics["roc_auc"] > 0.95  # the generated phishing names are easy to tell apart
    assert {"low", "uncertain", "high"} == set(metrics["bands"])
    assert "ROC AUC" in capsys.readouterr().out


def test_command_line_json(capsys):
    predict.main(["https://paypal-secure-login-verify.com", "github.com", "--json"])
    results = json.loads(capsys.readouterr().out)
    assert [r["level"] for r in results] == ["high", "official"]
    assert results[0]["reasons"][0]["contribution"] > 0
