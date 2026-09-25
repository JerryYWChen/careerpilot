import hashlib
import ipaddress
import re
import socket
import unicodedata
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from trafilatura import extract

from backend.models.analysis import Gap
from backend.rag.models import NormalizedKnowledgeSource
from backend.rag.web_models import (
    AuthorityRule,
    FetchedWebPage,
    SelectedWebSource,
    WebSearchResult,
)


MAX_FETCH_ATTEMPTS = 2
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_NORMALIZED_CHARS = 200_000
MIN_NORMALIZED_CHARS = 120
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


AUTHORITY_REGISTRY = (
    AuthorityRule(
        aliases=("docker", "docker containers"),
        allowed_host="docs.docker.com",
        source_type="official_documentation",
    ),
    AuthorityRule(
        aliases=("kubernetes", "k8s"),
        allowed_host="kubernetes.io",
        source_type="official_documentation",
        path_prefixes=("/docs/",),
    ),
    AuthorityRule(
        aliases=("python",),
        allowed_host="docs.python.org",
        source_type="official_documentation",
    ),
    AuthorityRule(
        aliases=("aws", "amazon web services"),
        allowed_host="docs.aws.amazon.com",
        source_type="official_documentation",
    ),
    AuthorityRule(
        aliases=("azure", "microsoft azure"),
        allowed_host="learn.microsoft.com",
        source_type="official_documentation",
        path_fragments=("/azure/",),
    ),
    AuthorityRule(
        aliases=("github actions",),
        allowed_host="docs.github.com",
        source_type="official_documentation",
        path_fragments=("/actions",),
    ),
    AuthorityRule(
        aliases=("terraform",),
        allowed_host="developer.hashicorp.com",
        source_type="official_documentation",
        path_fragments=("/terraform/",),
    ),
    AuthorityRule(
        aliases=("postgresql", "postgres"),
        allowed_host="postgresql.org",
        source_type="official_documentation",
        path_prefixes=("/docs/",),
    ),
)


class WebFetchError(RuntimeError):
    pass


class SourceExtractionError(RuntimeError):
    pass


class WebPageFetcher(Protocol):
    def fetch(self, source: SelectedWebSource) -> FetchedWebPage: ...


def _matches_phrase(text: str, phrase: str) -> bool:
    return bool(
        re.search(
            rf"(?<!\w){re.escape(phrase.casefold())}(?!\w)",
            text.casefold(),
        )
    )


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    if parsed.scheme.casefold() != "https" or not parsed.hostname:
        raise ValueError("Trusted source URLs must use HTTPS.")
    if parsed.username or parsed.password:
        raise ValueError("Trusted source URLs must not include credentials.")
    if parsed.port not in {None, 443}:
        raise ValueError("Trusted source URLs must not use a custom port.")

    hostname = parsed.hostname.rstrip(".").casefold()
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError("Trusted source URL contains an invalid hostname.") from error

    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in _TRACKING_PARAMETERS
    ]
    path = parsed.path or "/"
    return urlunsplit(("https", hostname, path, urlencode(query), ""))


def _host_matches(hostname: str, allowed_host: str) -> bool:
    hostname = hostname.casefold()
    allowed_host = allowed_host.casefold()
    return hostname == allowed_host or hostname.endswith(f".{allowed_host}")


def _path_matches(path: str, rule: AuthorityRule) -> bool:
    normalized_path = path.casefold()
    if rule.path_prefixes and not any(
        normalized_path.startswith(prefix.casefold())
        for prefix in rule.path_prefixes
    ):
        return False
    if rule.path_fragments and not any(
        fragment.casefold() in normalized_path
        for fragment in rule.path_fragments
    ):
        return False
    return True


def select_trusted_sources(
    gap: Gap,
    results: list[WebSearchResult],
    *,
    registry: tuple[AuthorityRule, ...] = AUTHORITY_REGISTRY,
    limit: int = MAX_FETCH_ATTEMPTS,
) -> list[SelectedWebSource]:
    if limit < 1:
        return []

    applicable_rules = [
        rule
        for rule in registry
        if any(_matches_phrase(gap.area, alias) for alias in rule.aliases)
    ]
    if not applicable_rules:
        return []

    selected: list[SelectedWebSource] = []
    seen_urls: set[str] = set()

    for result in sorted(results, key=lambda item: item.rank):
        try:
            canonical_url = canonicalize_url(result.url)
        except (TypeError, ValueError):
            continue

        parsed = urlsplit(canonical_url)
        candidate_text = " ".join(
            part for part in (result.title, result.snippet, parsed.path) if part
        )

        for rule in applicable_rules:
            if not _host_matches(parsed.hostname or "", rule.allowed_host):
                continue
            if not _path_matches(parsed.path, rule):
                continue
            if not any(
                _matches_phrase(candidate_text, alias) for alias in rule.aliases
            ):
                continue
            if canonical_url in seen_urls:
                break

            seen_urls.add(canonical_url)
            selected.append(
                SelectedWebSource(
                    result=result,
                    canonical_url=canonical_url,
                    rule=rule,
                )
            )
            break

        if len(selected) >= limit:
            break

    return selected


def _resolve_addresses(hostname: str) -> list[str]:
    return list(
        {
            row[4][0]
            for row in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        }
    )


def _validate_public_destination(
    url: str,
    *,
    rule: AuthorityRule,
    resolver: Callable[[str], list[str]],
) -> str:
    try:
        canonical_url = canonicalize_url(url)
    except (TypeError, ValueError) as error:
        raise WebFetchError(f"Fetch target URL was invalid: {error}") from error
    parsed = urlsplit(canonical_url)
    hostname = parsed.hostname or ""
    if not _host_matches(hostname, rule.allowed_host):
        raise WebFetchError("Fetch target left the trusted authority domain.")
    if not _path_matches(parsed.path, rule):
        raise WebFetchError("Fetch target left the trusted authority path.")

    try:
        addresses = resolver(hostname)
    except OSError as error:
        raise WebFetchError(f"Could not resolve fetch target: {error}") from error
    if not addresses:
        raise WebFetchError("Fetch target resolved to no network addresses.")

    for address in addresses:
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError as error:
            raise WebFetchError("Fetch target resolved to an invalid address.") from error
        if not parsed_address.is_global:
            raise WebFetchError("Fetch target resolved to a non-public address.")

    return canonical_url


class HttpxWebPageFetcher:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        resolver: Callable[[str], list[str]] = _resolve_addresses,
        clock: Callable[[], datetime] | None = None,
        max_redirects: int = MAX_REDIRECTS,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
    ) -> None:
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(8.0, connect=3.0),
            follow_redirects=False,
        )
        self.resolver = resolver
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.max_redirects = max_redirects
        self.max_response_bytes = max_response_bytes

    def fetch(self, source: SelectedWebSource) -> FetchedWebPage:
        current_url = source.canonical_url
        requested_url = current_url

        for redirect_count in range(self.max_redirects + 1):
            current_url = _validate_public_destination(
                current_url,
                rule=source.rule,
                resolver=self.resolver,
            )

            try:
                with self.client.stream(
                    "GET",
                    current_url,
                    headers={
                        "Accept": "text/html,text/plain;q=0.9",
                        "User-Agent": "CareerPilot-Knowledge/1.0",
                    },
                    follow_redirects=False,
                ) as response:
                    if response.status_code in _REDIRECT_STATUSES:
                        location = response.headers.get("location")
                        if not location:
                            raise WebFetchError("Redirect response had no location.")
                        if redirect_count >= self.max_redirects:
                            raise WebFetchError("Web page exceeded the redirect limit.")
                        current_url = urljoin(current_url, location)
                        continue

                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    media_type = content_type.split(";", 1)[0].strip().casefold()
                    if media_type not in {"text/html", "text/plain"}:
                        raise WebFetchError(
                            f"Unsupported web page content type: {media_type or 'unknown'}"
                        )

                    declared_length = response.headers.get("content-length")
                    if (
                        declared_length
                        and declared_length.isdigit()
                        and int(declared_length) > self.max_response_bytes
                    ):
                        raise WebFetchError("Web page exceeded the response size limit.")

                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > self.max_response_bytes:
                            raise WebFetchError(
                                "Web page exceeded the response size limit."
                            )

                    return FetchedWebPage(
                        requested_url=requested_url,
                        final_url=current_url,
                        content_type=media_type,
                        encoding=response.encoding or "utf-8",
                        body=bytes(body),
                        fetched_at=self.clock(),
                    )
            except WebFetchError:
                raise
            except httpx.HTTPError as error:
                raise WebFetchError(f"Web page fetch failed: {error}") from error

        raise WebFetchError("Web page exceeded the redirect limit.")


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("\r\n", "\n")
    value = value.replace("\r", "\n")
    lines = [line.rstrip() for line in value.splitlines()]
    normalized_lines: list[str] = []
    blank_count = 0

    for line in lines:
        if line.strip():
            blank_count = 0
            normalized_lines.append(line)
        else:
            blank_count += 1
            if blank_count <= 1:
                normalized_lines.append("")

    return "\n".join(normalized_lines).strip()


def normalize_web_page(
    source: SelectedWebSource,
    page: FetchedWebPage,
) -> NormalizedKnowledgeSource:
    try:
        canonical_final_url = canonicalize_url(page.final_url)
    except (TypeError, ValueError) as error:
        raise SourceExtractionError(
            f"Fetched page URL was invalid: {error}"
        ) from error
    parsed_final_url = urlsplit(canonical_final_url)
    if not _host_matches(
        parsed_final_url.hostname or "",
        source.rule.allowed_host,
    ) or not _path_matches(parsed_final_url.path, source.rule):
        raise SourceExtractionError(
            "Fetched page did not remain within the trusted authority scope."
        )

    try:
        decoded = page.body.decode(page.encoding, errors="replace")
    except LookupError:
        decoded = page.body.decode("utf-8", errors="replace")

    if page.content_type == "text/html":
        extracted = extract(
            decoded,
            output_format="markdown",
            include_comments=False,
            include_images=False,
            include_links=False,
            include_tables=True,
            favor_precision=True,
        )
        if not extracted:
            raise SourceExtractionError("No useful main content was extracted.")
    else:
        extracted = decoded

    title = _normalize_text(source.result.title)
    if not title:
        raise SourceExtractionError("Fetched page had no usable title.")
    content = _normalize_text(extracted)
    if not content.startswith("# "):
        content = f"# {title}\n\n{content}"

    if len(content) < MIN_NORMALIZED_CHARS:
        raise SourceExtractionError("Extracted content was too short to ingest.")
    if len(content) > MAX_NORMALIZED_CHARS:
        raise SourceExtractionError("Extracted content exceeded the size limit.")

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return NormalizedKnowledgeSource(
        title=title,
        canonical_url=canonical_final_url,
        source_type=source.rule.source_type,
        retrieved_at=page.fetched_at,
        last_checked_at=page.fetched_at,
        content=content,
        content_hash=content_hash,
    )
