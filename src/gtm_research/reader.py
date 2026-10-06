"""Public, exact-host website reader with pinned DNS and bounded HTTP reads."""

from dataclasses import dataclass, field
from copy import deepcopy
from datetime import datetime, timezone
from html.parser import HTMLParser
import http.client
import ipaddress
import math
import socket
import ssl
import truststore
from threading import Timer
from time import monotonic
from urllib.parse import urljoin, urlsplit, urlunsplit

from .bounds import bounded_call
from .schema import normalize_text


class ToolError(Exception):
    """A safe, fixed error code suitable for a model tool result."""

    def __init__(self, code, outcome=None):
        super().__init__(code)
        self.code = code
        self.outcome = outcome


def cacheable_failure(code):
    """Return whether unchanged reader settings make a retry repeatable."""
    if code in {
        "response_too_large", "unsupported_encoding", "invalid_response",
        "unsupported_content_type", "empty_page", "redirect_limit",
        "invalid_redirect", "blocked_downgrade", "blocked_address", "blocked_host",
    }:
        return True
    if code.startswith("http_"):
        try:
            status = int(code.removeprefix("http_"))
        except ValueError:
            return False
        return 400 <= status < 500 and status not in (408, 425, 429)
    return False


def canonical_url(value):
    if not isinstance(value, str) or not value or len(value) > 4000:
        raise ToolError("invalid_url")
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or "\\" in value:
        raise ToolError("invalid_url")
    try:
        parts = urlsplit(value)
        host = parts.hostname
        if parts.scheme not in ("http", "https") or not host or parts.username is not None or parts.password is not None:
            raise ValueError
        host = host.encode("idna").decode("ascii").lower()
        if host.endswith(".") or "%" in host:
            raise ValueError
        port = parts.port
        if port not in (None, 443 if parts.scheme == "https" else 80):
            raise ValueError
        netloc = f"[{host}]" if ":" in host else host
        return urlunsplit((parts.scheme, netloc, parts.path or "/", parts.query, ""))
    except (ValueError, UnicodeError):
        raise ToolError("invalid_url") from None


def start_url(domain):
    value = domain if "://" in domain else f"https://{domain}"
    return canonical_url(value)


def resolve_public(host, port, timeout):
    try:
        records = bounded_call(
            lambda: socket.getaddrinfo(host, port, type=socket.SOCK_STREAM), timeout
        )
        addresses = list(dict.fromkeys(record[4][0] for record in records))
        if not addresses:
            raise ToolError("dns_error")
        for address in addresses:
            ip = ipaddress.ip_address(address)
            # Reject mapped/tunnel forms rather than relying on platform-specific routing.
            if (not ip.is_global or ip.is_multicast or ip.is_reserved
                    or (isinstance(ip, ipaddress.IPv6Address) and
                        (ip.is_site_local or ip.ipv4_mapped or ip.sixtofour or ip.teredo
                         or ip in ipaddress.ip_network("64:ff9b::/96")
                         or ip in ipaddress.ip_network("64:ff9b:1::/48")))):
                raise ToolError("blocked_address")
        return addresses[0]
    except TimeoutError:
        raise ToolError("timeout") from None
    except (OSError, ValueError):
        raise ToolError("dns_error") from None


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes


def request(url, address, timeout, max_bytes):
    """Connect only to a vetted numeric address, retaining Host and TLS SNI.

    No proxy environment, cookies, auth, automatic redirects, or decompression.
    A watchdog closes the socket at the absolute request deadline, including
    slow headers and trickling bodies. The caller budgets redirects separately.
    """
    parts = urlsplit(url)
    port = 443 if parts.scheme == "https" else 80
    deadline = monotonic() + timeout
    conn = http.client.HTTPConnection(parts.hostname, port, timeout=timeout)
    raw = None
    timer = None
    status = None
    headers = {}
    declared = None
    data = bytearray()

    def fail(code, read_completed=False):
        raise ToolError(code, {
            "final_url": url,
            "http_status": status,
            "observed_bytes": len(data),
            "declared_content_length": declared,
            "read_completed": read_completed,
            "observed_bytes_kind": (
                "complete" if read_completed else "lower_bound" if data else "unavailable"
            ),
        })

    try:
        raw = socket.create_connection((address, port), timeout=timeout)
        remaining = deadline - monotonic()
        if remaining <= 0:
            fail("timeout")
        raw.settimeout(remaining)
        if parts.scheme == "https":
            raw = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT).wrap_socket(raw, server_hostname=parts.hostname)
        conn.sock = raw

        def expire():
            try:
                raw.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        remaining = deadline - monotonic()
        if remaining <= 0:
            fail("timeout")
        raw.settimeout(remaining)
        timer = Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        path = urlunsplit(("", "", parts.path or "/", parts.query, ""))
        conn.request("GET", path, headers={
            "User-Agent": "GTMAccountResearch/0.1", "Accept": "text/html, text/plain",
            "Accept-Encoding": "identity", "Connection": "close",
        })
        response = conn.getresponse()
        status = response.status
        headers = {key.lower(): value for key, value in response.getheaders()}
        if response.status in (301, 302, 303, 307, 308):
            return Response(response.status, headers, b"")
        if headers.get("content-encoding", "identity").lower() != "identity":
            fail("unsupported_encoding")
        length = headers.get("content-length")
        if length is not None:
            declared = length
            try:
                declared = int(length)
                if declared < 0:
                    fail("invalid_response")
                if declared > max_bytes:
                    fail("response_too_large")
            except ValueError:
                fail("invalid_response")
        while len(data) <= max_bytes:
            if monotonic() >= deadline:
                fail("timeout")
            chunk = response.read1(min(16384, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if monotonic() >= deadline:
            fail("timeout")
        if len(data) > max_bytes:
            fail("response_too_large")
        if declared is not None and len(data) != declared:
            fail("incomplete_response", read_completed=True)
        return Response(response.status, headers, bytes(data))
    except ToolError:
        raise
    except (TimeoutError, socket.timeout):
        fail("timeout")
    except (OSError, http.client.HTTPException):
        fail("timeout" if monotonic() >= deadline else "network_error")
    finally:
        if timer:
            timer.cancel()
        conn.close()
        if raw:
            raw.close()


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "template"):
            self.hidden.append(tag)
        if tag == "a" and not self.hidden:
            for key, value in attrs:
                if key == "href" and value and len(self.links) < 500:
                    self.links.append(value)

    def handle_endtag(self, tag):
        if self.hidden and tag == self.hidden[-1]:
            self.hidden.pop()

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


@dataclass
class WebsiteReader:
    domain: str
    timeout: float = 10.0
    max_bytes: int = 250_000
    max_redirects: int = 3
    resolver: object = resolve_public
    transport: object = request
    diagnostic_label: str | None = None
    allowed: set = field(init=False)
    pages: dict = field(default_factory=dict, init=False)
    outcomes: list = field(default_factory=list, init=False)
    failure_cache: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        if (not math.isfinite(self.timeout) or self.timeout <= 0 or self.max_bytes < 1
                or self.max_redirects < 0 or
                (self.diagnostic_label is not None and
                 (not isinstance(self.diagnostic_label, str) or len(self.diagnostic_label) > 100))):
            raise ValueError("Reader limits must be positive (redirects may be zero)")
        self.root = start_url(self.domain)
        self.host = urlsplit(self.root).hostname
        self.allowed = {self.root}

    def approve_host(self, url):
        url = canonical_url(url)
        if urlsplit(url).hostname != self.host:
            raise ToolError("blocked_host")
        return url

    def _cache_key(self, url):
        return (url, self.max_bytes, self.max_redirects)

    def untried_allowed_urls(self):
        return sorted(
            url for url in self.allowed
            if url not in self.pages and self._cache_key(url) not in self.failure_cache
        )

    def _base_outcome(self, requested_url, final_url=None):
        outcome = {
            "requested_url": requested_url,
            "final_url": final_url,
            "redirects": [],
            "max_bytes": self.max_bytes,
            "observed_bytes": 0,
            "declared_content_length": None,
            "read_completed": False,
            "observed_bytes_kind": "unavailable",
            "http_status": None,
            "status": "failed",
            "error": None,
            "cached": False,
            "network_attempted": False,
        }
        if self.diagnostic_label is not None:
            outcome["measurement_context"] = self.diagnostic_label
        return outcome

    def _raise_recorded(self, code, outcome, cache_key=None):
        outcome.update(status="failed", error=code)
        if cache_key is not None and cacheable_failure(code):
            self.failure_cache[cache_key] = deepcopy(outcome)
        self.outcomes.append(deepcopy(outcome))
        raise ToolError(code, deepcopy(outcome))

    def fetch(self, url, timeout=None):
        try:
            url = canonical_url(url)
        except ToolError as exc:
            outcome = self._base_outcome(None)
            self._raise_recorded(exc.code, outcome)
        if urlsplit(url).hostname != self.host:
            outcome = self._base_outcome(url, url)
            self._raise_recorded("blocked_host", outcome)
        if url not in self.allowed:
            outcome = self._base_outcome(url, url)
            self._raise_recorded("undiscovered_url", outcome)
        if url in self.pages:
            page = self.pages[url]
            outcome = self._base_outcome(url, page["url"])
            outcome.update(
                status="success", error=None, cached=True,
                redirects=deepcopy(page["redirects"]),
                observed_bytes=page["bytes"],
                declared_content_length=page["declared_content_length"],
                read_completed=True, observed_bytes_kind="complete", http_status=200,
            )
            self.outcomes.append(outcome)
            return page
        cache_key = self._cache_key(url)
        if cache_key in self.failure_cache:
            outcome = deepcopy(self.failure_cache[cache_key])
            outcome.update(cached=True, network_attempted=False)
            self.outcomes.append(deepcopy(outcome))
            raise ToolError(outcome["error"], outcome)
        original = url
        outcome = self._base_outcome(original, url)
        deadline = monotonic() + min(self.timeout, timeout if timeout is not None else self.timeout)
        redirects = []
        try:
            for hop in range(self.max_redirects + 1):
                outcome.update(final_url=url, redirects=deepcopy(redirects))
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise ToolError("timeout")
                parts = urlsplit(url)
                outcome["network_attempted"] = True
                address = self.resolver(parts.hostname, 443 if parts.scheme == "https" else 80, remaining)
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise ToolError("timeout")
                response = self.transport(url, address, remaining, self.max_bytes)
                outcome.update(
                    final_url=url, http_status=response.status,
                    observed_bytes=len(response.body), read_completed=True,
                    observed_bytes_kind="complete", declared_content_length=None,
                )
                length = response.headers.get("content-length")
                if length is not None:
                    try:
                        outcome["declared_content_length"] = int(length)
                    except ValueError:
                        outcome["declared_content_length"] = length
                if monotonic() >= deadline:
                    raise ToolError("timeout")
                if response.status in (301, 302, 303, 307, 308):
                    outcome["read_completed"] = False
                    outcome["observed_bytes_kind"] = "unavailable"
                    if hop == self.max_redirects:
                        raise ToolError("redirect_limit")
                    location = response.headers.get("location")
                    if not location:
                        raise ToolError("invalid_redirect")
                    target_value = urljoin(url, location)
                    try:
                        target = self.approve_host(target_value)
                    except ToolError as exc:
                        try:
                            outcome["final_url"] = canonical_url(target_value)
                        except ToolError:
                            pass
                        raise exc
                    if parts.scheme == "https" and urlsplit(target).scheme != "https":
                        outcome["final_url"] = target
                        raise ToolError("blocked_downgrade")
                    redirects.append({"status": response.status, "from": url, "to": target})
                    url = target
                    continue
                if response.status != 200:
                    raise ToolError(f"http_{response.status}")
                if len(response.body) > self.max_bytes:
                    outcome["read_completed"] = False
                    outcome["observed_bytes_kind"] = "lower_bound"
                    raise ToolError("response_too_large")
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if content_type not in ("text/html", "text/plain", "application/xhtml+xml"):
                    raise ToolError("unsupported_content_type")
                text = response.body.decode("utf-8", errors="replace")
                links = []
                if content_type != "text/plain":
                    parser = PageParser()
                    parser.feed(text)
                    text = " ".join(parser.parts)
                    links = parser.links
                text = normalize_text(text)
                if not text:
                    raise ToolError("empty_page")
                discovered = set()
                for link in links:
                    try:
                        discovered.add(self.approve_host(urljoin(url, link)))
                    except (ToolError, ValueError):
                        continue
                self.allowed.update(discovered | {url})
                page = {
                    "url": url, "requested_url": original, "text": text,
                    "links": sorted(discovered), "redirects": redirects,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "bytes": len(response.body),
                    "declared_content_length": outcome["declared_content_length"],
                    "read_completed": True,
                    "observed_bytes_kind": "complete",
                }
                outcome.update(status="success", error=None, redirects=deepcopy(redirects))
                self.outcomes.append(deepcopy(outcome))
                self.pages[original] = page
                self.pages[url] = page
                return page
        except ToolError as exc:
            if exc.outcome:
                for key in ("final_url", "http_status", "observed_bytes",
                            "declared_content_length", "read_completed",
                            "observed_bytes_kind"):
                    if key in exc.outcome:
                        outcome[key] = exc.outcome[key]
            outcome["redirects"] = deepcopy(redirects)
            self._raise_recorded(exc.code, outcome, cache_key)
        raise AssertionError("reader loop exited without a result")
