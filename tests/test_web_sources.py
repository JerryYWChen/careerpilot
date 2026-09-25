import hashlib
from datetime import datetime, timezone

import httpx
import pytest

from backend.models.analysis import Gap, MatchStatus
from backend.rag.web_models import FetchedWebPage, WebSearchResult
from backend.rag.web_sources import (
    AUTHORITY_REGISTRY,
    HttpxWebPageFetcher,
    WebFetchError,
    canonicalize_url,
    normalize_web_page,
    select_trusted_sources,
)


NOW = datetime(2026, 9, 23, 16, 0, tzinfo=timezone.utc)


def _gap(area: str) -> Gap:
    return Gap(
        area=area,
        status=MatchStatus.MISSING,
        reason="No resume evidence.",
    )


def _result(url: str, *, title: str = "Docker official documentation", rank: int = 1):
    return WebSearchResult(
        title=title,
        url=url,
        snippet="Docker documentation and getting started guidance.",
        rank=rank,
        provider="test",
    )


def test_initial_authority_registry_is_intentionally_small_and_exact() -> None:
    assert [rule.aliases for rule in AUTHORITY_REGISTRY] == [
        ("docker", "docker containers"),
        ("kubernetes", "k8s"),
        ("python",),
        ("aws", "amazon web services"),
        ("azure", "microsoft azure"),
        ("github actions",),
        ("terraform",),
        ("postgresql", "postgres"),
    ]
    assert [rule.allowed_host for rule in AUTHORITY_REGISTRY] == [
        "docs.docker.com",
        "kubernetes.io",
        "docs.python.org",
        "docs.aws.amazon.com",
        "learn.microsoft.com",
        "docs.github.com",
        "developer.hashicorp.com",
        "postgresql.org",
    ]


def test_selector_accepts_official_domain_and_rejects_lookalike() -> None:
    results = [
        _result("https://docs.docker.com.evil.example/get-started/", rank=1),
        _result(
            "https://docs.docker.com/get-started/?utm_source=test#section",
            rank=2,
        ),
    ]

    selected = select_trusted_sources(_gap("Docker"), results)

    assert len(selected) == 1
    assert selected[0].canonical_url == "https://docs.docker.com/get-started/"
    assert selected[0].rule.source_type == "official_documentation"


def test_selector_enforces_path_constraints_and_unknown_authorities() -> None:
    kubernetes_results = [
        _result(
            "https://kubernetes.io/blog/release/",
            title="Kubernetes release blog",
            rank=1,
        ),
        _result(
            "https://kubernetes.io/docs/tutorials/",
            title="Kubernetes tutorials",
            rank=2,
        ),
    ]

    selected = select_trusted_sources(_gap("Kubernetes"), kubernetes_results)

    assert [item.canonical_url for item in selected] == [
        "https://kubernetes.io/docs/tutorials/"
    ]
    assert select_trusted_sources(_gap("React"), kubernetes_results) == []


def test_fetcher_follows_only_validated_same_authority_redirects() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "/guide"})
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><body><article>Docker guide content.</article></body></html>",
        )

    selected = select_trusted_sources(
        _gap("Docker"),
        [_result("https://docs.docker.com/start")],
    )[0]
    fetcher = HttpxWebPageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=lambda hostname: ["93.184.216.34"],
        clock=lambda: NOW,
    )

    page = fetcher.fetch(selected)

    assert requests == [
        "https://docs.docker.com/start",
        "https://docs.docker.com/guide",
    ]
    assert page.final_url == "https://docs.docker.com/guide"
    assert page.fetched_at == NOW


def test_fetcher_rejects_private_destinations_before_request() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, text="should not be reached")

    selected = select_trusted_sources(
        _gap("Docker"),
        [_result("https://docs.docker.com/start")],
    )[0]
    fetcher = HttpxWebPageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=lambda hostname: ["127.0.0.1"],
    )

    with pytest.raises(WebFetchError, match="non-public"):
        fetcher.fetch(selected)

    assert called is False


def test_fetcher_rejects_redirect_outside_authority() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            302,
            headers={"location": "https://evil.example/docker"},
        )

    selected = select_trusted_sources(
        _gap("Docker"),
        [_result("https://docs.docker.com/start")],
    )[0]
    fetcher = HttpxWebPageFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        resolver=lambda hostname: ["93.184.216.34"],
    )

    with pytest.raises(WebFetchError, match="authority domain"):
        fetcher.fetch(selected)

    assert request_count == 1


def test_fetcher_rejects_oversized_response() -> None:
    selected = select_trusted_sources(
        _gap("Docker"),
        [_result("https://docs.docker.com/start")],
    )[0]
    fetcher = HttpxWebPageFetcher(
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    headers={"content-type": "text/html"},
                    content=b"x" * 101,
                )
            )
        ),
        resolver=lambda hostname: ["93.184.216.34"],
        max_response_bytes=100,
    )

    with pytest.raises(WebFetchError, match="size limit"):
        fetcher.fetch(selected)


def test_html_extraction_builds_checkpoint_one_source() -> None:
    selected = select_trusted_sources(
        _gap("Docker"),
        [_result("https://docs.docker.com/get-started/")],
    )[0]
    body = b"""
        <html><body>
          <nav>Unrelated navigation menu</nav>
          <main>
            <h1>Docker getting started</h1>
            <p>Docker packages an application and its dependencies into a container image.</p>
            <h2>Practice</h2>
            <p>Build an image, run the container locally, inspect its logs, and document the commands used.</p>
          </main>
          <script>ignore_this_script()</script>
        </body></html>
    """
    page = FetchedWebPage(
        requested_url=selected.canonical_url,
        final_url=selected.canonical_url,
        content_type="text/html",
        encoding="utf-8",
        body=body,
        fetched_at=NOW,
    )

    source = normalize_web_page(selected, page)

    assert source.canonical_url == selected.canonical_url
    assert source.source_type == "official_documentation"
    assert "Docker packages an application" in source.content
    assert "ignore_this_script" not in source.content
    assert source.retrieved_at == NOW
    assert source.last_checked_at == NOW
    assert source.content_hash == hashlib.sha256(
        source.content.encode("utf-8")
    ).hexdigest()


def test_url_canonicalization_rejects_credentials_and_non_https() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        canonicalize_url("http://docs.docker.com/start")
    with pytest.raises(ValueError, match="credentials"):
        canonicalize_url("https://user:pass@docs.docker.com/start")
