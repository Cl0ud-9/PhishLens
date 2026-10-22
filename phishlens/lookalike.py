"""Typosquats: names made to be misread as a brand's own, such as paypa1, g00gle or rnicrosoft.

The model judges how a name looks in general, and "paypa1" looks as ordinary as any name; what gives it away is that
it is one keystroke from "paypal". This compares a registered name with the names of the official brand domains in
official.py. Like that list, it runs before the model, and the reported accuracy does not use it.
"""
from dataclasses import dataclass

from .official import OFFICIAL

# Characters that read like a letter, longest first. Applied to a name before comparing it with the brands' names.
CONFUSABLE = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("3", "e"), ("5", "s"), ("7", "t"), ("4", "a"),
              ("8", "b"), ("9", "g")]
# Names shorter than this are too short to compare: "dhl" is one edit from hundreds of real names
MIN_LENGTH = 5


def _name(domain):
    return domain.split(".", 1)[0]


# Brand name -> (its official domain, the brand). The first official domain listed for a name is used in messages.
BRAND_NAMES = {}
for _domain, _brand in OFFICIAL.items():
    BRAND_NAMES.setdefault(_name(_domain), (_domain, _brand))


@dataclass(frozen=True)
class LookAlike:
    kind: str     # "disguised": reads as the brand once look-alike characters are read as letters
                  # "one_edit": one letter added, removed, changed or swapped
                  # "other_ending": the brand's exact name on an ending its official domain does not use
    domain: str   # the official domain it resembles
    brand: str


def read_as_letters(name):
    """The name as it reads at a glance: 'g00gle' -> 'google', 'rnicrosoft' -> 'microsoft'."""
    for chars, letter in CONFUSABLE:
        name = name.replace(chars, letter)
    return name


def edit_distance(a, b, limit=2):
    """Damerau-Levenshtein distance (adjacent swaps count as one edit), or limit + 1 once it is clearly larger."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    before, previous = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                current[j] = min(current[j], before[j - 2] + 1)
        before, previous = previous, current
    return min(previous[-1], limit + 1)


def find(name, registered_domain):
    """The brand a registered name imitates, or None. Official domains themselves never match."""
    if registered_domain in OFFICIAL or len(name) < MIN_LENGTH:
        return None
    if name in BRAND_NAMES:
        domain, brand = BRAND_NAMES[name]
        return LookAlike("other_ending", domain, brand)
    disguised = read_as_letters(name)
    if disguised != name and disguised in BRAND_NAMES:
        return LookAlike("disguised", *BRAND_NAMES[disguised])
    for brand_name, (domain, brand) in BRAND_NAMES.items():
        if len(brand_name) >= MIN_LENGTH and edit_distance(name, brand_name, limit=1) == 1:
            return LookAlike("one_edit", domain, brand)
    return None
