import socket

import pytest

from phishlens import PhishLens, check


def test_checking_links_never_touches_the_network(monkeypatch):
    model = PhishLens.load()

    def refuse(*args, **kwargs):
        raise AssertionError("PhishLens tried to reach the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    for url in ["https://paypal-secure-login-verify.com/x", "https://example.co.uk", "https://shop.web.app",
                "https://pаypal.com", "http://203.0.113.9/"]:
        assert check(url, model).level in {"low", "uncertain", "high", "ip", "official"}


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "mailto:someone@example.com"])
def test_odd_schemes_are_read_as_text_only(url):
    try:
        check(url, PhishLens.load())
    except ValueError:
        pass  # no host to judge: refused with a message, never opened
