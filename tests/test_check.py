import pytest

from phishlens import PhishLens, check
from phishlens.model import SHARED_HOSTING_AS


@pytest.fixture(scope="module")
def model():
    return PhishLens.load()


def test_ip_address(model):
    v = check("http://203.0.113.9/bank/login.php", model)
    assert v.level == "ip" and v.score is None


@pytest.mark.parametrize("url", ["https://mail.google.com/mail/u/0/", "github.com/Cl0ud-9", "https://www.onlinesbi.sbi"])
def test_official_domains(model, url):
    assert check(url, model).level == "official"


def test_official_list_needs_the_real_registered_domain(model):
    v = check("https://google.com.account-check.xyz/", model)
    assert v.level != "official"
    assert any("really belongs to account-check.xyz" in n for n in v.notes)


def test_shared_hosting_is_explained_and_not_held_against_the_site(model):
    v = check("https://my-portfolio.vercel.app/", model)
    assert any("anyone can publish" in n for n in v.notes)
    assert all(f".{SHARED_HOSTING_AS}" in r.text for r in v.reasons if r.feature in ("suffix", "suffix_levels"))
    same_on_com = check("https://my-portfolio.com/", model)
    assert v.score == pytest.approx(same_on_com.score)


def test_look_alike_letters_are_warned_about(model):
    v = check("https://pаypal.com/", model)
    assert any("look-alike letters" in n for n in v.notes)


def test_reasons_are_ordered_by_size(model):
    sizes = [abs(r.contribution) for r in check("https://secure-update-account-2024.top/", model).reasons]
    assert sizes == sorted(sizes, reverse=True) and len(sizes) == 6
