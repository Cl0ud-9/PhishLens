import pytest

from phishlens.domains import parse, to_unicode


@pytest.mark.parametrize("url, host, domain", [
    ("https://www.example.com/login?x=1", "www.example.com", "example.com"),
    ("example.com/path", "example.com", "example.com"),
    ("HTTPS://EXAMPLE.COM:8443/", "example.com", "example.com"),
    ("https://bank.example.co.uk/", "bank.example.co.uk", "example.co.uk"),
    ("https://example.com./", "example.com", "example.com"),
])
def test_registered_domain(url, host, domain):
    h = parse(url)
    assert (h.host, h.registered_domain) == (host, domain)
    assert not h.shared_hosting and not h.is_ip


def test_the_at_sign_trick_is_seen_through():
    assert parse("https://google.com@evil-site.xyz/login").registered_domain == "evil-site.xyz"


def test_a_long_host_belongs_to_its_registered_domain():
    h = parse("https://accounts.google.com.verify-session.top/")
    assert (h.name, h.suffix) == ("verify-session", "top")


@pytest.mark.parametrize("url", ["http://192.168.1.10/login", "http://[2001:db8::1]/", "8.8.8.8"])
def test_ip_addresses(url):
    assert parse(url).is_ip


def test_shared_hosting_judges_the_site():
    h = parse("https://my-shop.web.app/")
    assert h.shared_hosting and (h.name, h.suffix) == ("my-shop", "web.app")


def test_look_alike_letters_become_punycode():
    h = parse("https://pаypal.com/")  # Cyrillic а
    assert h.name.startswith("xn--")
    assert to_unicode(h.host) == "pаypal.com"


@pytest.mark.parametrize("url", ["", "   ", "http://", "https:///path"])
def test_no_host(url):
    with pytest.raises(ValueError):
        parse(url)
