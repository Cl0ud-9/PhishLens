"""The PhiUSIIL Phishing URL dataset, reduced to one row per registered domain."""
import hashlib
import urllib.request
from pathlib import Path

import pandas as pd

from .domains import parse

URL = "https://archive.ics.uci.edu/static/public/967/data.csv"
SHA256 = "a236549cd369cd80bd478ff8e1779cbf44c58d5c3f79f7a51a1adbed7d06d1c6"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "PhiUSIIL_Phishing_URL_Dataset.csv"


def download(path=DATA_PATH):
    """Download the dataset from the UCI repository and check it is the expected file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=120) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise ValueError(f"downloaded file has SHA-256 {digest}, expected {SHA256}")
    path.write_bytes(data)
    return path


def load_urls(path=DATA_PATH):
    """URLs and labels. In PhiUSIIL label 1 means legitimate; here phishing is 1."""
    raw = pd.read_csv(path, usecols=["URL", "label"], encoding="utf-8-sig")
    return pd.DataFrame({"url": raw["URL"], "phishing": 1 - raw["label"]}).drop_duplicates("url")


def to_domains(urls):
    """One row per registered domain.

    Every legitimate URL in the dataset is a bare https://www.<domain> home page, so anything beyond the registered
    domain would teach the model the dataset's format instead of phishing. Shared-hosting sites are left out, since
    the dataset has no legitimate ones to learn from, and so are domains that appear with both labels.
    """
    hosts = urls["url"].map(parse)
    frame = pd.DataFrame({
        "name": hosts.map(lambda h: h.name), "suffix": hosts.map(lambda h: h.suffix),
        "shared": hosts.map(lambda h: h.shared_hosting), "ip": hosts.map(lambda h: h.is_ip),
        "phishing": urls["phishing"].to_numpy(),
    })
    kept = frame[~frame["shared"] & ~frame["ip"] & (frame["name"] != "") & (frame["suffix"] != "")]
    domains = kept.groupby(["name", "suffix"], as_index=False)["phishing"].agg(["mean", "size"])
    clean = domains[domains["mean"].isin([0, 1])].rename(columns={"mean": "phishing", "size": "urls"})
    clean["phishing"] = clean["phishing"].astype(int)
    stats = {"urls": len(urls), "shared_hosting_urls": int(frame["shared"].sum()), "ip_urls": int(frame["ip"].sum()),
             "mixed_label_domains": int(len(domains) - len(clean)), "domains": len(clean),
             "phishing_domains": int(clean["phishing"].sum())}
    return clean.reset_index(drop=True), stats
