# Changelog

What changed in each version of PhishLens.

The format follows [Keep a Changelog](https://keepachangelog.com), and the versions follow
[Semantic Versioning](https://semver.org).

## [1.0.0] - 2026-10-22

The first version.

### Added

- Judging a link by its registered domain: name features, a letter-pattern score and the domain's ending, combined by
  LightGBM, with each feature's SHAP value from LightGBM's built-in TreeSHAP.
- Finding the real domain with the public-suffix list, seeing through `user@host` links, and making look-alike letters
  visible as punycode.
- Recognising official domains of commonly imitated brands, flagging bare IP addresses, and judging shared-hosting
  sites by their own name.
- `app.py` (Streamlit), `predict.py` (command line, text or JSON) and `train.py`, which downloads PhiUSIIL, checks it,
  trains, measures on unseen domains and explains the model's mistakes with SHAP.
- `scripts/url_shortcut.py`, which shows why the whole URL cannot be used with this dataset.
- The model saved as plain files that load without running code, tests, continuous integration on Python 3.11 to
  3.14, and the license, notice, contributing, conduct and security files.
