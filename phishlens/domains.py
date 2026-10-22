"""Read a URL's host and split it into its registered name and public suffix. Nothing is ever fetched."""
import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit

import tldextract

# The public-suffix list bundled with tldextract: no download, no cache. Private entries are included, so shared
# hosting such as web.app counts as a suffix and each site on it as its own domain.
_extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None, include_psl_private_domains=True)


@dataclass(frozen=True)
class Host:
    url: str               # the URL as read, with a scheme added if it had none
    host: str              # the host name, lower case, in its ASCII (punycode) form
    name: str              # the registered name: "paypal" in paypal.co.uk, or the site's name on shared hosting
    suffix: str            # the public suffix, such as "co.uk", or the hosting platform, such as "web.app"
    shared_hosting: bool   # on a platform where anyone can publish
    is_ip: bool            # a bare IP address instead of a name

    @property
    def registered_domain(self):
        return f"{self.name}.{self.suffix}" if self.name and self.suffix else self.host


def to_ascii(host):
    """Write a host the way DNS sees it, so look-alike letters show up as xn-- punycode."""
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError:
        return host


def to_unicode(host):
    """Write a punycode host the way a browser may show it."""
    try:
        return host.encode("ascii").decode("idna")
    except UnicodeError:
        return host


def parse(url):
    """Split a URL into the parts PhishLens judges. Raises ValueError if it has no host."""
    text = url.strip()
    if not text:
        raise ValueError("the URL is empty")
    if "://" not in text:
        text = "http://" + text  # "example.com/login" has no scheme, but is still a URL
    host = to_ascii((urlsplit(text).hostname or "").rstrip(".").lower())
    if not host:
        raise ValueError(f"there is no host name in {url!r}")
    try:
        ipaddress.ip_address(host)
        return Host(text, host, "", "", shared_hosting=False, is_ip=True)
    except ValueError:
        pass
    parts = _extract(host)
    return Host(text, host, parts.domain, parts.suffix, shared_hosting=parts.is_private, is_ip=False)
