"""Judge one URL: a verdict, a risk score and the reasons behind it."""
from dataclasses import dataclass, field

from .domains import parse, to_unicode
from .features import COLUMNS, describe
from .model import SHARED_HOSTING_AS
from .official import OFFICIAL

# Score bands. The README reports how often each band was right on domains the model never saw.
LOW, HIGH = 0.3, 0.7


@dataclass
class Reason:
    feature: str
    text: str
    contribution: float  # SHAP value in log-odds: above 0 raises the risk, below 0 lowers it


@dataclass
class Verdict:
    url: str
    host: str
    domain: str
    level: str                 # "official", "low", "uncertain", "high" or "ip"
    summary: str
    score: float | None = None  # probability of phishing, from the model
    reasons: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def check(url, model, top=6):
    """Judge a URL from its text alone. It is never opened."""
    host = parse(url)
    if host.is_ip:
        return Verdict(url, host.host, host.host, "ip", "High risk: a bare IP address instead of a name",
                       notes=["Legitimate sites almost always use a name. An IP address hides who runs the site."])
    if host.registered_domain in OFFICIAL:
        brand = OFFICIAL[host.registered_domain]
        return Verdict(url, host.host, host.registered_domain, "official", f"Official {brand} domain",
                       notes=[f"{host.registered_domain} is on PhishLens's list of official brand domains."])

    frame = model.frame([host.name], [host.suffix], [host.shared_hosting])
    score = float(model.score(frame)[0])
    shap = model.contributions(frame)[0]
    order = sorted(range(len(COLUMNS)), key=lambda i: -abs(shap[i]))[:top]
    reasons = [Reason(COLUMNS[i], describe(COLUMNS[i], frame.iloc[0, i], host.name, host.suffix), float(shap[i]))
               for i in order]
    if host.shared_hosting:
        for r in reasons:
            if r.feature in ("suffix", "suffix_levels"):
                r.text = (f"Scored as if it ended in .{SHARED_HOSTING_AS}, "
                          "since the platform says nothing about the site")
    if score >= HIGH:
        level, summary = "high", "High risk: this domain looks like the ones phishers register"
    elif score >= LOW:
        level, summary = "uncertain", "Uncertain: some signs of phishing, not enough to be sure"
    else:
        level, summary = "low", "Low risk: this domain looks like a genuine site's"
    notes = []
    if "xn--" in host.host:
        shown = to_unicode(host.host)
        notes.append(f"Warning: this name uses non-Latin or look-alike letters. It shows as {shown} but is really "
                     f"{host.host}. Phishers use this to imitate familiar names letter for letter.")
    if host.shared_hosting:
        notes.append(f"{host.suffix} is a hosting platform where anyone can publish. Only the site's name, "
                     f'"{host.name}", is judged; the platform itself says nothing about who runs the site.')
    if host.host != host.registered_domain and host.host.removeprefix("www.") != host.registered_domain:
        notes.append(f"The address really belongs to {host.registered_domain}. Everything before it "
                     f"({host.host.removesuffix('.' + host.registered_domain)}) can be chosen freely by its owner.")
    return Verdict(url, host.host, host.registered_domain, level, summary, score, reasons, notes)
