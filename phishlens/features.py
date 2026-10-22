"""What PhishLens measures about a domain's name, and how to say it in words."""
import collections
import math

# Names phishers borrow to look trustworthy
BRANDS = ("paypal", "apple", "icloud", "microsoft", "office", "outlook", "amazon", "netflix", "facebook", "instagram",
          "whatsapp", "google", "gmail", "coinbase", "metamask", "binance", "dhl", "fedex", "usps", "chase",
          "wellsfargo", "hsbc", "sbi", "hdfc", "icici", "adobe", "docusign", "dropbox", "linkedin", "twitter", "yahoo")
# Words that ask the reader to act
ACTION_WORDS = ("login", "logon", "signin", "secure", "verify", "account", "update", "support", "service", "wallet",
                "bank", "pay", "auth", "confirm", "recovery", "billing", "invoice", "unlock", "suspend", "alert",
                "delivery", "refund", "bonus", "gift", "claim", "prize", "airdrop", "connect", "sync", "validate")
VOWELS = set("aeiou")

# Model inputs, in order. "suffix" is categorical; "name_pattern" comes from the letter-pattern model.
NUMERIC = ["length", "digits", "digit_ratio", "hyphens", "vowel_ratio", "consonant_run", "entropy", "unique_ratio",
           "brand_exact", "brand_inside", "action_words", "punycode", "suffix_levels"]
COLUMNS = NUMERIC + ["suffix", "name_pattern"]


def entropy(text):
    """Shannon entropy of the characters, in bits: random-looking strings score high."""
    counts = collections.Counter(text)
    n = len(text)
    return -sum(c / n * math.log2(c / n) for c in counts.values()) if n else 0.0


def name_features(name, suffix=""):
    """Numeric features of a registered name such as "paypal-login" (without its suffix)."""
    n = len(name) or 1
    letters = [c for c in name if c.isalpha()]
    run = longest = 0
    for c in name:
        run = run + 1 if c.isalpha() and c not in VOWELS else 0
        longest = max(longest, run)
    return {
        "length": len(name),
        "digits": sum(c.isdigit() for c in name),
        "digit_ratio": sum(c.isdigit() for c in name) / n,
        "hyphens": name.count("-"),
        "vowel_ratio": sum(c in VOWELS for c in letters) / max(len(letters), 1),
        "consonant_run": longest,
        "entropy": entropy(name),
        "unique_ratio": len(set(name)) / n,
        "brand_exact": int(name in BRANDS),
        "brand_inside": int(name not in BRANDS and any(b in name for b in BRANDS)),
        "action_words": sum(w in name for w in ACTION_WORDS),
        "punycode": int(name.startswith("xn--")),
        "suffix_levels": suffix.count(".") + 1 if suffix else 0,
    }


def describe(feature, value, name, suffix):
    """A sentence about one feature of this domain, for the explanation."""
    found = lambda words: ", ".join(f'"{w}"' for w in words if w in name)  # noqa: E731
    if feature == "length":
        return f"The name is {int(value)} characters long"
    if feature == "digits":
        return f"The name has {int(value)} digit{'s' if value != 1 else ''}"
    if feature == "digit_ratio":
        return f"Digits make up {value:.0%} of the name"
    if feature == "hyphens":
        return f"The name has {int(value)} hyphen{'s' if value != 1 else ''}"
    if feature == "vowel_ratio":
        return f"Vowels make up {value:.0%} of its letters"
    if feature == "consonant_run":
        return f"The longest run of consonants is {int(value)}"
    if feature == "entropy":
        return f"Character variety (entropy) is {value:.2f} bits"
    if feature == "unique_ratio":
        return f"{value:.0%} of its characters are different from each other"
    if feature == "brand_exact":
        return "The name is exactly a well-known brand" if value else "The name is not a well-known brand"
    if feature == "brand_inside":
        return (f"The name contains a brand ({found(BRANDS)}) without being that brand" if value
                else "The name does not borrow a brand")
    if feature == "action_words":
        return (f"It contains words that ask you to act: {found(ACTION_WORDS)}" if value
                else "No 'login', 'verify'-type words")
    if feature == "punycode":
        return ("It is written in punycode (xn--), which can hide look-alike letters" if value
                else "It uses plain letters")
    if feature == "suffix_levels":
        return f"The suffix has {int(value)} part{'s' if value != 1 else ''}"
    if feature == "suffix":
        return f"It ends in .{suffix}" if suffix else "Its ending is not judged (shared hosting)"
    if feature == "name_pattern":
        return f"Its letter patterns score {value:.2f} on resembling phishing names (0 to 1)"
    raise KeyError(feature)
