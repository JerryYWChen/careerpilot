import os
import re
from typing import Protocol

import httpx

from backend.models.analysis import Gap
from backend.rag.web_models import WebSearchResult


BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
MAX_SEARCH_RESULTS = 5
MAX_QUERY_CHARS = 200
_MAX_REQUIREMENT_CHARS = 140
_UNSAFE_QUERY_CHARS = re.compile(r"[^\w\s.+#/-]", flags=re.UNICODE)


class WebSearchError(RuntimeError):
    pass


class WebSearchProvider(Protocol):
    def search(self, query: str, *, limit: int) -> list[WebSearchResult]: ...


def build_web_search_query(gap: Gap) -> str:
    requirement = " ".join(gap.area.split())
    requirement = _UNSAFE_QUERY_CHARS.sub(" ", requirement)
    requirement = " ".join(requirement.split())[:_MAX_REQUIREMENT_CHARS].strip()
    if not requirement:
        raise ValueError("Gap area must contain searchable text.")

    query = f'"{requirement}" official documentation getting started'
    return query[:MAX_QUERY_CHARS]


class BraveWebSearchProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY is required.")
        self.client = client or httpx.Client(timeout=8.0)

    def search(self, query: str, *, limit: int) -> list[WebSearchResult]:
        if not query.strip():
            raise ValueError("Search query must not be empty.")
        if limit < 1 or limit > MAX_SEARCH_RESULTS:
            raise ValueError(f"Search limit must be between 1 and {MAX_SEARCH_RESULTS}.")

        try:
            response = self.client.get(
                BRAVE_SEARCH_ENDPOINT,
                params={
                    "q": query,
                    "count": limit,
                    "safesearch": "strict",
                    "search_lang": "en",
                },
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise WebSearchError(f"Brave search failed: {error}") from error

        if not isinstance(payload, dict):
            raise WebSearchError("Brave search returned an invalid response payload.")
        web_payload = payload.get("web", {})
        if not isinstance(web_payload, dict):
            raise WebSearchError("Brave search returned an invalid web payload.")
        raw_results = web_payload.get("results", [])
        if not isinstance(raw_results, list):
            raise WebSearchError("Brave search returned an invalid results payload.")

        results: list[WebSearchResult] = []
        for item in raw_results:
            if len(results) >= limit:
                break
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            url = item.get("url")
            snippet = item.get("description")
            if not isinstance(title, str) or not title.strip():
                continue
            if not isinstance(url, str) or not url.strip():
                continue
            if snippet is not None and not isinstance(snippet, str):
                snippet = None

            results.append(
                WebSearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if snippet else None,
                    rank=len(results) + 1,
                    provider="brave",
                )
            )

        return results
