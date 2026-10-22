"""PhishLens: does this link's domain look like a phishing domain, and why."""
from .check import Verdict, check
from .domains import parse
from .model import PhishLens

__all__ = ["PhishLens", "Verdict", "check", "parse"]
__version__ = "1.0.0"
