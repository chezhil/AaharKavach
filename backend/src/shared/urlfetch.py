"""Fetch a product webpage safely.

Two things this guards against:

* **SSRF.** A QR code is attacker-controlled input. Without checks, a scanned
  code could point the server at ``http://169.254.169.254/...`` — the instance
  metadata service — and exfiltrate IAM credentials, or at anything else on the
  private network. Every resolved address is checked, on the original URL *and
  on every redirect hop*, so a public host cannot bounce us onto a private one.
* **Resource exhaustion.** Responses are capped rather than read whole.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

MAX_BYTES = 512 * 1024
TIMEOUT_SECONDS = 6
ALLOWED_SCHEMES = {"http", "https"}
# Product URLs redirect constantly — Open Food Facts 302s to add the product
# slug, and printed QR codes usually go through a shortener. Refusing outright
# made the feature fail on its most ordinary input, so hops are followed and
# each one is re-checked instead.
MAX_REDIRECTS = 4


class UnsafeUrl(ValueError):
    """The URL points somewhere we refuse to fetch from."""


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    """Follow redirects, but re-run the safety check on every hop.

    Refusing redirects outright is the easy way to stop a public host bouncing
    us onto a private one, but it also refuses the ordinary case. Validating
    each new URL keeps the guarantee: no hop reaches a private address, whoever
    issued it.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        assert_safe(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


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


#: How much of the page top to keep: enough for the title, brand and heading,
#: which is where the product's name is.
HEAD_CHARS = 700
#: Marks the cut so the reader does not run the two pieces into one sentence.
_WINDOW_JOIN = "\n[…]\n"

#: "Ingredients", "Ingrédients", "INGREDIENTS:" — the heading that introduces
#: the list we actually want.
_INGREDIENTS_HEADING = re.compile(r"ingr[eé]dien(?:ts?|tes)\b", re.IGNORECASE)


def best_window(text: str, max_chars: int) -> str:
    """The slice of a page most likely to contain the ingredient list.

    Taking the first ``max_chars`` of a real product page returns navigation,
    cookie banners and marketing copy. On an Open Food Facts product page the
    word "ingredients" first appears about 2,000 characters in as part of a
    Nutri-Score explainer, while the list itself starts near 7,600 — so a
    4,000-character head window reliably handed the reader everything except
    the one thing it was asked to find, and every scan of a real URL came back
    "we couldn't find an ingredient list on that page".

    A heading followed by several commas is a list; one followed by prose is
    not. The window is centred on the best candidate — and the top of the page
    is kept in front of it, because that is where the product's name and brand
    are. Centring on the list alone read the ingredients correctly and then
    reported them under "Product from page".
    """
    if len(text) <= max_chars:
        return text

    best_start: int | None = None
    best_commas = 2  # a real list has more separators than this
    for match in _INGREDIENTS_HEADING.finditer(text):
        commas = text[match.start() : match.start() + 240].count(",")
        if commas > best_commas:
            best_commas, best_start = commas, match.start()

    if best_start is None:
        return text[:max_chars]

    head_chars = min(HEAD_CHARS, max_chars // 4)
    head = text[:head_chars]
    body_budget = max_chars - len(head) - len(_WINDOW_JOIN)
    start = max(head_chars, best_start - body_budget // 6)
    body = text[start : start + body_budget]
    return head + _WINDOW_JOIN + body


def fetch_text(url: str, max_chars: int = 4000) -> str:
    """Fetch a page and return its visible text. Raises UnsafeUrl or URLError."""
    assert_safe(url)
    opener = urllib.request.build_opener(_CheckedRedirects)
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
    return best_window(stripper.text(), max_chars)
