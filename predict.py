"""Check links from the command line: does each domain look like a phishing domain, and why. Links are never opened."""
import argparse
import json
from dataclasses import asdict

from phishlens import PhishLens, check


def show(verdict):
    score = f" ({verdict.score:.0%})" if verdict.score is not None else ""
    lines = [f"{verdict.url}", f"  {verdict.summary}{score}", f"  domain judged: {verdict.domain}"]
    for r in verdict.reasons:
        arrow = "raises" if r.contribution > 0 else "lowers"
        lines.append(f"    {arrow} risk {abs(r.contribution):4.2f}  {r.text}")
    lines += [f"  note: {n}" for n in verdict.notes]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="one or more links, with or without https://")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)
    model = PhishLens.load()
    results = []
    for url in args.urls:
        try:
            results.append(check(url, model))
        except ValueError as error:
            parser.error(str(error))
    if args.json:
        print(json.dumps([asdict(v) for v in results], indent=2))
    else:
        print("\n\n".join(show(v) for v in results))


if __name__ == "__main__":
    main()
