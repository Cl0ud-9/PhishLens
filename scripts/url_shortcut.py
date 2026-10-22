"""Why PhishLens judges the domain only: a model on whole URLs scores very well on PhiUSIIL and learns nothing useful.

Every legitimate URL in the dataset is a bare https://www.<domain> home page, so simple facts about the URL's shape
separate the classes almost perfectly. This trains such a model, measures it on domains it never saw, and asks it about
some ordinary genuine links.
"""
import sys
from pathlib import Path
from urllib.parse import urlsplit

import lightgbm as lgb
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from phishlens.data import DATA_PATH, download, load_urls  # noqa: E402
from phishlens.domains import parse  # noqa: E402

GENUINE = ["https://github.com/Cl0ud-9", "https://mail.google.com/mail/u/0/", "https://en.wikipedia.org/wiki/Phishing",
           "https://www.amazon.in/gp/cart"]


def shape(url):
    parts = urlsplit(url)
    return [len(url), url.startswith("https"), "://www." in url, len(parts.path.strip("/")), len(parts.query),
            url.count("-"), sum(c.isdigit() for c in url)]


def main():
    if not DATA_PATH.exists():
        download()
    urls = load_urls()
    x = np.array([shape(u) for u in urls["url"]], dtype=float)
    groups = urls["url"].map(lambda u: parse(u).registered_domain)
    train, test = next(GroupShuffleSplit(1, test_size=0.25, random_state=0).split(x, urls["phishing"], groups))
    y = urls["phishing"].to_numpy()
    model = lgb.LGBMClassifier(n_estimators=200, verbose=-1).fit(x[train], y[train])
    p = model.predict_proba(x[test])[:, 1]
    print(f"Whole-URL model on unseen domains: accuracy {accuracy_score(y[test], p > 0.5):.4f}, "
          f"ROC AUC {roc_auc_score(y[test], p):.4f}")
    for url in GENUINE:
        print(f"  {url:42} phishing probability {model.predict_proba(np.array([shape(url)], dtype=float))[0, 1]:.3f}")


if __name__ == "__main__":
    main()
