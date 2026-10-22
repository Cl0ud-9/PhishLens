# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub: open the [Security tab](https://github.com/Cl0ud-9/PhishLens/security) and choose
**Report a vulnerability**, or go straight to
[the advisory form](https://github.com/Cl0ud-9/PhishLens/security/advisories/new). Only the maintainer sees what you
send.

Please include what you found, how to reproduce it, and what you think an attacker could do with it. The maintainer
aims to answer within a week, and you will be credited in the fix unless you would rather not be.

## What counts

- A link that makes PhishLens open it, contact it, or reach the network in any way. It must only ever read the text.
- A link that makes the app or `predict.py` run code, read files, or hang.
- A way to make PhishLens report the wrong registered domain, for example calling `evil.example` `google.com`.
- A model file that runs code when loaded. Models are plain text, a NumPy array loaded without pickle, and JSON, and
  should stay that way.

Not in scope: a single link scored wrongly (see the README's *Honest limits*), and problems in LightGBM, scikit-learn,
tldextract or Streamlit themselves (report those upstream).

## Supported versions

Only the current `main` gets fixes.
