import pytest

from phishlens import PhishLens, check
from phishlens.lookalike import edit_distance, find, read_as_letters


@pytest.fixture(scope="module")
def model():
    return PhishLens.load()


@pytest.mark.parametrize("name, reads_as", [("g00gle", "google"), ("paypa1", "paypal"), ("rnicrosoft", "microsoft"),
                                            ("vvhatsapp", "whatsapp")])
def test_look_alike_characters_are_read_as_letters(name, reads_as):
    assert read_as_letters(name) == reads_as


@pytest.mark.parametrize("a, b, distance", [("paypal", "paypal", 0), ("paypai", "paypal", 1), ("payapl", "paypal", 1),
                                            ("paypall", "paypal", 1), ("pypl", "paypal", 2), ("google", "amazon", 3)])
def test_edit_distance(a, b, distance):
    assert edit_distance(a, b) == distance


@pytest.mark.parametrize("url, domain", [("https://g00gle.com/login", "google.com"), ("paypa1.com", "paypal.com"),
                                         ("https://rnicrosoft.net/", "microsoft.com")])
def test_disguised_names_are_high_risk(model, url, domain):
    v = check(url, model)
    assert v.level == "lookalike"
    assert domain in v.summary
    assert v.reasons  # the model's own reasons are still shown


def test_one_letter_away_is_never_called_low_risk(model):
    v = check("https://paypai.com/", model)
    assert v.level in ("uncertain", "high")
    assert any("one letter away from paypal.com" in n for n in v.notes)


def test_same_name_on_another_ending_is_only_noted(model):
    v = check("https://amazon.de/", model)
    assert v.level != "lookalike"
    assert any("amazon.com" in n for n in v.notes)


@pytest.mark.parametrize("url", ["https://www.google.com", "https://paypal.com/signin", "https://www.viit.ac.in",
                                 "https://github.com/Cl0ud-9", "https://example.com"])
def test_genuine_and_unrelated_names_are_not_flagged(model, url):
    v = check(url, model)
    assert v.level != "lookalike"
    assert not any("one letter away" in n for n in v.notes)


def test_short_brand_names_are_not_compared():
    assert find("dhls", "dhls.com") is None  # one letter from "dhl", like countless real names
