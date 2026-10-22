"""Train PhishLens on the PhiUSIIL dataset, measure it on domains it never saw, and explain its mistakes with SHAP."""
import argparse
import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from phishlens import __version__
from phishlens.check import HIGH, LOW
from phishlens.data import DATA_PATH, download, load_urls, to_domains
from phishlens.features import COLUMNS
from phishlens.model import MODEL_DIR, PhishLens
from phishlens.pattern import NamePattern

PARAMS = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 40,
          "feature_fraction": 0.9, "bagging_fraction": 0.9, "bagging_freq": 1, "seed": 0, "verbose": -1}
ROUNDS = 500
TOP_SUFFIXES = 60


def out_of_fold_pattern(names, labels, folds=5):
    """Letter-pattern scores for the training domains, each from a model that did not see that domain."""
    scores = np.zeros(len(names))
    for fit, held in StratifiedKFold(folds, shuffle=True, random_state=0).split(names, labels):
        scores[held] = NamePattern.fit(names[fit], labels[fit]).score(names[held])
    return scores


def bands(y, p):
    """How often each score band was right."""
    out = {}
    for name, mask in [("low", p < LOW), ("uncertain", (p >= LOW) & (p < HIGH)), ("high", p >= HIGH)]:
        out[name] = {"domains": int(mask.sum()), "share": float(mask.mean()),
                     "phishing_rate": float(y[mask].mean()) if mask.any() else None}
    return out


def error_analysis(frame, y, p, contrib, threshold=0.5):
    """Which features pushed the model wrong: mean SHAP value per feature among false positives and negatives."""
    result = {}
    kinds = [("false_positives", (p >= threshold) & (y == 0)), ("false_negatives", (p < threshold) & (y == 1))]
    for kind, mask in kinds:
        if not mask.any():
            result[kind] = {"count": 0, "mean_shap": {}}
            continue
        mean = pd.Series(contrib[mask, :-1].mean(axis=0), index=COLUMNS).sort_values(key=abs, ascending=False)
        result[kind] = {"count": int(mask.sum()), "mean_shap": {k: round(float(v), 4) for k, v in mean.items()}}
    return result


def figures(frame, contrib, errors, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory.mkdir(parents=True, exist_ok=True)
    importance = pd.Series(np.abs(contrib[:, :-1]).mean(axis=0), index=COLUMNS).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(importance.index, importance.values, color="#5b4bd5")
    ax.set_xlabel("mean |SHAP value| (log-odds)")
    ax.set_title("What PhishLens relies on, over all test domains")
    fig.tight_layout()
    fig.savefig(directory / "shap_importance.png", dpi=150)
    plt.close(fig)

    fp = pd.Series(errors["false_positives"]["mean_shap"])
    fn = pd.Series(errors["false_negatives"]["mean_shap"])
    order = (fp.abs() + fn.abs()).sort_values().index
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(np.arange(len(order)) + 0.2, fp[order], height=0.4, label="false positives (genuine, called phishing)",
            color="#c0392b")
    ax.barh(np.arange(len(order)) - 0.2, fn[order], height=0.4, label="false negatives (phishing, called genuine)",
            color="#2e7d32")
    ax.set_yticks(np.arange(len(order)), order)
    ax.axvline(0, color="#555", linewidth=0.8)
    ax.set_xlabel("mean SHAP value (log-odds): right raises the risk, left lowers it")
    ax.set_title("What pushed the model wrong")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(directory / "shap_errors.png", dpi=150)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=DATA_PATH, help="the PhiUSIIL CSV; downloaded if missing")
    parser.add_argument("--out", default=MODEL_DIR, help="where to save the model")
    parser.add_argument("--figures", default=None, help="folder for the SHAP charts (needs matplotlib)")
    args = parser.parse_args(argv)

    from pathlib import Path
    if not Path(args.data).exists():
        print("Downloading the PhiUSIIL dataset from UCI (57 MB)...")
        download(args.data)
    domains, stats = to_domains(load_urls(args.data))
    print(f"{stats['urls']:,} URLs -> {stats['domains']:,} registered domains "
          f"({stats['phishing_domains']:,} phishing); left out: {stats['shared_hosting_urls']:,} shared-hosting URLs, "
          f"{stats['ip_urls']:,} IP addresses, {stats['mixed_label_domains']:,} domains with both labels")

    names, y = domains["name"].to_numpy(), domains["phishing"].to_numpy()
    train, test = train_test_split(np.arange(len(domains)), test_size=0.25, stratify=y, random_state=0)
    suffixes = domains["suffix"].iloc[train].value_counts().index[:TOP_SUFFIXES].tolist()

    pattern = NamePattern.fit(names[train], y[train])
    model = PhishLens(None, pattern, suffixes)
    x_train = model.frame(names[train], domains["suffix"].iloc[train].tolist())
    x_train["name_pattern"] = out_of_fold_pattern(names[train], y[train])
    x_test = model.frame(names[test], domains["suffix"].iloc[test].tolist())

    model.booster = lgb.train(PARAMS, lgb.Dataset(x_train, y[train], categorical_feature=["suffix"]), ROUNDS)
    p = model.score(x_test)
    contrib = model.contributions(x_test)
    tn, fp, fn, tp = confusion_matrix(y[test], p >= 0.5).ravel()
    errors = error_analysis(x_test, y[test], p, contrib)
    metrics = {
        "version": __version__, "data": stats, "train_domains": len(train), "test_domains": len(test),
        "roc_auc": float(roc_auc_score(y[test], p)), "average_precision": float(average_precision_score(y[test], p)),
        "pattern_only_roc_auc": float(roc_auc_score(y[test], x_test["name_pattern"])),
        "at_0.5": {"precision": float(tp / (tp + fp)), "recall": float(tp / (tp + fn)),
                   "accuracy": float((tp + tn) / len(test)), "confusion": {"tn": int(tn), "fp": int(fp),
                                                                             "fn": int(fn), "tp": int(tp)}},
        "bands": bands(y[test], p), "errors": errors,
    }
    model.metadata = {"version": __version__, "lightgbm": lgb.__version__, "roc_auc": round(metrics["roc_auc"], 4)}
    model.save(args.out)
    (Path(args.out) / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if args.figures:
        figures(x_test, contrib, errors, Path(args.figures))

    print(f"Test domains: {len(test):,}. ROC AUC {metrics['roc_auc']:.4f} "
          f"(letter patterns alone {metrics['pattern_only_roc_auc']:.4f}), average precision "
          f"{metrics['average_precision']:.4f}")
    a = metrics["at_0.5"]
    print(f"At 0.5: precision {a['precision']:.3f}, recall {a['recall']:.3f}, accuracy {a['accuracy']:.3f}")
    for name, b in metrics["bands"].items():
        rate = f"{b['phishing_rate']:.1%} of them phishing" if b["phishing_rate"] is not None else "none"
        print(f"  {name:9} {b['share']:6.1%} of domains, {rate}")
    for kind, e in errors.items():
        top = ", ".join(f"{k} ({v:+.2f})" for k, v in list(e["mean_shap"].items())[:3])
        print(f"  {kind}: {e['count']:,}" + (f"; pushed by {top}" if top else ""))


if __name__ == "__main__":
    main()
