# Contributing to PhishLens

Thanks for wanting to help. Bug reports, ideas and pull requests are all welcome. Please keep to the
[code of conduct](CODE_OF_CONDUCT.md).

The project is source-available, not open source: see [LICENSE](LICENSE). You may fork this repository to prepare
contributions, but not to publish or share your own copies. By opening a pull request you agree to clause 8 of the
license: you have the right to submit the change, and it becomes part of the project under the author's terms.

## Before you start

- **Found a bug?** Search the [issues](https://github.com/Cl0ud-9/PhishLens/issues) first, then open one.
- **A link judged wrongly?** That is expected sometimes (see the README's *Honest limits*). An issue is still welcome
  when you can see a pattern, such as a whole kind of genuine domain being rated high risk.
- **Have an idea?** Open an issue before writing code, so we can agree on the approach. Large changes that were not
  discussed may be closed.
- **Found a security problem?** Do not open a public issue. Report it privately: see [SECURITY.md](SECURITY.md).

## Setup

Requirements: Python 3.11, 3.12, 3.13 or 3.14.

```bash
git clone https://github.com/<your-account>/PhishLens.git
cd PhishLens
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
pytest
```

The tests need no dataset.

## What a pull request needs

- `ruff check .` and `pytest` pass.
- A new behaviour comes with a test that fails without it.
- A model change is measured with `python train.py --figures docs/img` on the same split, and the README's results are
  updated. Never let anything beyond the registered domain into the features: see *Why only the domain*.
- An addition to `phishlens/official.py` is a brand's own domain, checked at the source.
- No dataset files are committed.

## Style

Match the surrounding code. Comments are short and explain why, not what. Plain wording in docs and in the app, with
no marketing language.
