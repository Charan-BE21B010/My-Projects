from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

from importer_engine.llm import LLMClient
from importer_engine.models import RawCandidate
from importer_engine.query_planner import plan_queries


NOISE_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "reddit.com",
    "wikipedia.org",
    "linkedin.com",
    "pinterest.com",
    "tiktok.com",
    "amazon.com",
    "amazon.de",
    "ebay.com",
    "ebay.de",
    "alibaba.com",
    "indiamart.com",
    "made-in-china.com",
    "tradeindia.com",
    "craigslist.org",
    "indeed.com",
    "glassdoor.com",
    "bloomberg.com",
    "reuters.com",
    "worldatlas.com",
    "deutschland.de",
    "germany.travel",
    "britannica.com",
    "statista.com",
    "tripadvisor.com",
    "booking.com",
    "expedia.com",
    "yelp.com",
    "yellowpages.com",
    "crunchbase.com",
    "zoominfo.com",
    "dunbradstreet.com",
    "kompass.com",
    "europages.com",
    "europages.co.uk",
    "thomasnet.com",
    "google.com",
    "bing.com",
    "duckduckgo.com",
    "tradekey.com",
    "infobanc.com",
    "volza.com",
    "go4worldbusiness.com",
    "turkishexporter.net",
    "esources.co.uk",
    "usimportdata.com",
    "usacustomsclearance.com",
    "ceramictilesinfo.com",
    "importers-directory.net",
    "tradeimex.in",
    "exportgenius.com",
    "importyeti.com",
    "panjiva.com",
    "zauba.com",
    "eximpedia.app",
    "trademo.com",
    "yellowpages-uae.com",
    "yellowpages.com",
    "atninfo.com",
    "hindgate.com",
    "exportbusinessmart.com",
    "seair.co.in",
    "yp-uae.com",
    "unicotiles.com",
    "deutsche-steinzeug.de",
    "researchgate.net",
    "worldstopexports.com",
    "textileinfomedia.com",
    "alnadimexim.com",
    "l-tile.com",
    "acomiceramic.com",
    "pvrmines.com",
    "beddingtextilepro.com",
    "gildan.com",
    "tradologie.com",
}


IMPORTER_HINTS = re.compile(
    r"\b(import(?:er|s|ing)?|distributor|wholesale|wholesaler|trading|"
    r"handel|großhandel|grosshandel|einkauf|buyer|procurement)\b",
    re.I,
)


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _is_noise(url: str) -> bool:
    d = _domain(url)
    if not d:
        return True
    return any(d == n or d.endswith("." + n) for n in NOISE_DOMAINS)


def _guess_name(title: str, url: str) -> str:
    title = (title or "").strip()
    if title:
        # Common patterns: "Company | Tagline", "Company - Home"
        for sep in [" | ", " - ", " -- ", " :: "]:
            if sep in title:
                left = title.split(sep)[0].strip()
                if 2 <= len(left) <= 80:
                    return left
        if len(title) <= 90:
            return title
    d = _domain(url)
    return d.split(".")[0].replace("-", " ").title() if d else "Unknown"


def search_web(queries: list[str], max_per_query: int = 8) -> list[dict]:
    """Run DuckDuckGo text search. Soft-fail if network/lib issues."""
    results: list[dict] = []
    ddgs_cls = None
    try:
        from ddgs import DDGS as ddgs_cls  # type: ignore
    except ImportError:
        try:
            from duckduckgo_search import DDGS as ddgs_cls  # type: ignore
        except ImportError:
            return results

    try:
        with ddgs_cls() as ddgs:
            for q in queries:
                try:
                    hits = list(ddgs.text(q, max_results=max_per_query))
                except Exception:
                    hits = []
                for h in hits:
                    results.append(
                        {
                            "title": h.get("title") or "",
                            "href": h.get("href") or h.get("link") or "",
                            "body": h.get("body") or h.get("snippet") or "",
                            "query": q,
                        }
                    )
    except Exception:
        return results
    return results


def _extract_with_llm(
    product: str,
    country: str,
    hits: list[dict],
    llm: LLMClient,
) -> list[RawCandidate]:
    compact = [
        {
            "title": h["title"][:120],
            "url": h["href"],
            "snippet": h["body"][:220],
        }
        for h in hits[:40]
    ]
    data = llm.complete_json(
        system=(
            "You extract importer / wholesale distributor companies from search "
            "hits for an Indian exporter entering a foreign market. "
            "Exclude pure manufacturers that do not buy, exclude marketplaces, "
            "exclude news articles and job boards. "
            'Return JSON: {"companies":[{"name":"","website":"","snippet":"",'
            '"source_url":"","is_importer_likely":true}]}'
        ),
        user=(
            f"Product: {product}\nCountry: {country}\nHits:\n{compact}"
        ),
    )
    out: list[RawCandidate] = []
    for c in data.get("companies", []):
        if not c.get("is_importer_likely", True):
            continue
        name = (c.get("name") or "").strip()
        website = (c.get("website") or c.get("source_url") or "").strip()
        if not name or not website:
            continue
        if _is_noise(website):
            continue
        out.append(
            RawCandidate(
                name=name,
                website=website,
                snippet=(c.get("snippet") or "")[:400],
                source_url=c.get("source_url") or website,
                source_label="web_search+llm",
            )
        )
    return out


def _extract_heuristic(hits: list[dict]) -> list[RawCandidate]:
    out: list[RawCandidate] = []
    for h in hits:
        url = h.get("href") or ""
        if not url or _is_noise(url):
            continue
        title = h.get("title") or ""
        body = h.get("body") or ""
        blob = f"{title} {body}"
        # Prefer pages that look like company/importer pages
        if not IMPORTER_HINTS.search(blob) and "wholesale" not in blob.lower():
            # still keep company-looking domains with product relevance later
            path = urlparse(url).path or "/"
            if path not in {"/", ""} and len(path) > 40:
                continue
        out.append(
            RawCandidate(
                name=_guess_name(title, url),
                website=f"{urlparse(url).scheme}://{urlparse(url).netloc}",
                snippet=body[:400],
                source_url=url,
                source_label="web_search",
            )
        )
    return out


def dedupe_candidates(candidates: list[RawCandidate]) -> list[RawCandidate]:
    by_domain: dict[str, RawCandidate] = {}
    for c in candidates:
        key = _domain(c.website or c.source_url) or c.name.lower()
        if key not in by_domain:
            by_domain[key] = c
        else:
            # keep richer snippet
            if len(c.snippet) > len(by_domain[key].snippet):
                by_domain[key] = c
    return list(by_domain.values())


def discover_candidates(
    product: str,
    country: str,
    llm: Optional[LLMClient] = None,
) -> tuple[list[RawCandidate], list[str]]:
    queries = plan_queries(product, country, llm=llm)
    hits = search_web(queries)
    if not hits:
        return [], queries

    if llm and llm.available:
        try:
            cands = _extract_with_llm(product, country, hits, llm)
            if cands:
                return dedupe_candidates(cands), queries
        except Exception:
            pass

    return dedupe_candidates(_extract_heuristic(hits)), queries