"""Fetch a product webpage safely.

Two things this guards against:

* **SSRF.** A QR code is attacker-controlled input. Without checks, a scanned
  code could point the server at ``http://169.254.169.254/...`` — the instance
  metadata service — and exfiltrate IAM credentials, or at anything else on the
  private network. Every resolved address is checked, and redirects are refused
  so a public host cannot bounce us onto a private one.
* **Resource exhaustion.** Responses are capped rather than read whole.
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

MAX_BYTES = 512 * 1024
TIMEOUT_SECONDS = 6
ALLOWED_SCHEMES = {"http", "https"}


class UnsafeUrl(ValueError):
    """The URL points somewhere we refuse to fetch from."""


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise UnsafeUrl("This link redirects, which we don't follow for safety")


def _is_public(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local      # 169.254.0.0/16 — instance metadata lives here
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def assert_safe(url: str) -> str:
    """Raise UnsafeUrl unless every address this host resolves to is public."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeUrl("Only http and https links can be scanned")
    if not parsed.hostname:
        raise UnsafeUrl("That link has no hostname")

    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 0, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeUrl("That hostname could not be resolved") from exc

    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise UnsafeUrl("That hostname could not be resolved")
    for address in addresses:
        if not _is_public(address):
            raise UnsafeUrl("That link points to a private address, so we won't open it")
    return url


class _Stripper(HTMLParser):
    """Keep visible text, drop markup, scripts, styles and page furniture."""

    SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg", "form"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._depth += 1

    def handle_endtag(self, tag):
        # Counted, not a boolean: nested skipped tags used to re-enable capture
        # on the first closing tag.
        if tag in self.SKIP and self._depth:
            self._depth -= 1

    def handle_data(self, data):
        if not self._depth and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def fetch_text(url: str, max_chars: int = 4000) -> str:
    """Fetch a page and return its visible text. Raises UnsafeUrl or URLError."""
    assert_safe(url)
    opener = urllib.request.build_opener(_NoRedirects)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AaharKavach/1.0 (+product label reader)"},
    )
    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        ctype = (response.headers.get("Content-Type") or "").lower()
        if "html" not in ctype and "text" not in ctype:
            raise UnsafeUrl("That link isn't a web page")
        raw = response.read(MAX_BYTES)

    stripper = _Stripper()
    stripper.feed(raw.decode("utf-8", errors="ignore"))
    return stripper.text()[:max_chars]
