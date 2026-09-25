from urllib.parse import parse_qs

import httpx
import pytest

from backend.models.analysis import Gap, MatchStatus
from backend.rag.web_search import (
    BRAVE_SEARCH_ENDPOINT,
    BraveWebSearchProvider,
    build_web_search_query,
)


def _gap() -> Gap:
    return Gap(
        area="Docker containerization",
        status=MatchStatus.PARTIAL,
        evidence="PRIVATE_RESUME_EVIDENCE",
        reason="PRIVATE_MATCH_REASON",
    )


def test_search_query_uses_only_gap_area() -> None:
    query = build_web_search_query(_gap())

    assert "Docker containerization" in query
    assert "official documentation" in query
    assert "PRIVATE_RESUME_EVIDENCE" not in query
    assert "PRIVATE_MATCH_REASON" not in query
    assert "partial" not in query


def test_search_query_removes_operator_punctuation_and_control_characters() -> None:
    gap = Gap(
        area='Docker\nsite:private.example "secret"',
        status=MatchStatus.MISSING,
        reason="No evidence.",
    )

    query = build_web_search_query(gap)

    assert "\n" not in query
    assert '"secret"' not in query
    assert "site:private.example" not in query


def test_brave_provider_maps_and_caps_results() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {
                            "title": f"Docker result {index}",
                            "url": f"https://docs.docker.com/page-{index}",
                            "description": f"Description {index}",
                        }
                        for index in range(7)
                    ]
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = BraveWebSearchProvider(api_key="test-key", client=client)

    results = provider.search("docker official docs", limit=5)

    assert len(results) == 5
    assert [result.rank for result in results] == [1, 2, 3, 4, 5]
    assert all(result.provider == "brave" for result in results)
    assert captured_request is not None
    assert str(captured_request.url).startswith(BRAVE_SEARCH_ENDPOINT)
    assert captured_request.headers["x-subscription-token"] == "test-key"
    query = parse_qs(captured_request.url.query.decode())
    assert query["q"] == ["docker official docs"]
    assert query["count"] == ["5"]
    assert query["safesearch"] == ["strict"]


def test_brave_provider_rejects_limits_outside_shared_contract() -> None:
    provider = BraveWebSearchProvider(
        api_key="test-key",
        client=httpx.Client(transport=httpx.MockTransport(lambda request: None)),
    )

    with pytest.raises(ValueError, match="between 1 and 5"):
        provider.search("docker", limit=6)
