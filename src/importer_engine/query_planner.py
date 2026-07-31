from __future__ import annotations

from typing import Optional

from importer_engine.llm import LLMClient


COUNTRY_TLD = {
    "germany": "de",
    "deutschland": "de",
    "united arab emirates": "ae",
    "uae": "ae",
    "dubai": "ae",
    "united states": "us",
    "usa": "us",
    "united kingdom": "uk",
    "uk": "uk",
    "france": "fr",
    "netherlands": "nl",
    "australia": "au",
    "canada": "ca",
    "saudi arabia": "sa",
    "singapore": "sg",
}


def country_tld(country: str) -> str:
    return COUNTRY_TLD.get(country.strip().lower(), "com")


def plan_queries(
    product: str,
    country: str,
    llm: Optional[LLMClient] = None,
    max_queries: int = 6,
) -> list[str]:
    """Build focused search queries. Prefer LLM when available."""
    tld = country_tld(country)
    base = [
        f"{product} importer {country}",
        f"{product} distributor wholesale {country}",
        f"{product} importer buyer {country}",
        f'"{product}" importer OR wholesaler site:.{tld}',
        f"{product} import company {country} contact",
        f"{country} {product} B2B distributor",
    ]

    cl = country.strip().lower()
    pl = product.strip().lower()
    if "german" in cl or cl == "deutschland":
        if "tile" in pl or "ceramic" in pl or "fliesen" in pl:
            base.extend(
                [
                    "Fliesen Importeur Deutschland",
                    "Fliesen Grosshandel Deutschland",
                ]
            )
    if cl in {"uae", "united arab emirates", "dubai"}:
        base.append(f"{product} importer Dubai UAE")
    if cl in {"usa", "united states", "us"}:
        base.append(f"{product} wholesale importer USA")

    if llm and llm.available:
        try:
            data = llm.complete_json(
                system=(
                    "You plan web search queries to find genuine importer / "
                    "wholesale distributor companies (not manufacturers, not "
                    "marketplaces like Alibaba). Return JSON: "
                    '{"queries": ["...", "..."]} with 5-7 short queries.'
                ),
                user=(
                    f"Product: {product}\nTarget country: {country}\n"
                    "Prefer queries that surface company websites and trade "
                    "directories. Avoid news and job listings."
                ),
            )
            llm_queries = [q.strip() for q in data.get("queries", []) if q and q.strip()]
            if llm_queries:
                merged: list[str] = []
                seen: set[str] = set()
                for q in llm_queries + base:
                    key = q.lower()
                    if key not in seen:
                        seen.add(key)
                        merged.append(q)
                return merged[:max_queries]
        except Exception:
            pass

    out: list[str] = []
    seen: set[str] = set()
    for q in base:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out[:max_queries]