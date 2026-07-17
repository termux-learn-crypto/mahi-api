import requests
import json
from .config import config


class SearchEngine:
    def __init__(self):
        self.api_key = config.SEARCH_API_KEY
        self.providers = {
            "google": "https://www.googleapis.com/customsearch/v1",
            "duckduckgo": "https://api.duckduckgo.com/",
        }

    def search(self, query: str, num_results: int = 5) -> dict:
        results = self._search_duckduckgo(query, num_results)
        if results:
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "source": "web",
            }
        return {
            "query": query,
            "results": [],
            "count": 0,
            "source": "web",
            "message": "Koi results nahi mile.",
        }

    def _search_duckduckgo(self, query: str, num_results: int) -> list[dict]:
        try:
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": 1}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", query),
                        "snippet": data.get("AbstractText", ""),
                        "url": data.get("AbstractURL", ""),
                        "source": "duckduckgo",
                    })
                for topic in data.get("RelatedTopics", [])[:num_results - len(results)]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "duckduckgo",
                        })
                return results[:num_results]
        except Exception:
            pass
        return []

    def search_news(self, query: str, num_results: int = 5) -> list[dict]:
        try:
            if config.NEWS_API_KEY:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query,
                    "apiKey": config.NEWS_API_KEY,
                    "language": "en",
                    "sortBy": "relevancy",
                    "pageSize": num_results,
                }
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    articles = resp.json().get("articles", [])
                    return [
                        {
                            "title": a.get("title", ""),
                            "snippet": a.get("description", ""),
                            "url": a.get("url", ""),
                            "source": a.get("source", {}).get("name", ""),
                        }
                        for a in articles
                    ]
        except Exception:
            pass
        return self._fallback_news_search(query, num_results)

    def _fallback_news_search(self, query: str, num_results: int) -> list[dict]:
        results = self.search(f"{query} news latest", num_results)
        return results.get("results", [])

    def get_answer(self, query: str) -> str:
        ddg_result = self._search_duckduckgo(query, 1)
        if ddg_result:
            return ddg_result[0].get("snippet", "")
        return f"Mujhe \"{query}\" ke baare mein specific info nahi mili."
