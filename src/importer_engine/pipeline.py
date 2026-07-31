from __future__ import annotations

from datetime import datetime, timezone

from importer_engine.config import get_settings
from importer_engine.discovery import discover_candidates
from importer_engine.enricher import enrich_many
from importer_engine.llm import LLMClient
from importer_engine.models import DiscoveryRequest, DiscoveryResult
from importer_engine.ranker import rank_importers
from importer_engine.query_planner import plan_queries
from importer_engine.seed_fallback import seed_candidates_for


def run_discovery(
    req: DiscoveryRequest,
    use_seed_fallback: bool = True,
    seed_only: bool = False,
) -> DiscoveryResult:
    """
    End-to-end pipeline:
    1) plan queries
    2) search + extract candidates (unless seed_only)
    3) enrich contacts from company sites
    4) score and rank
    """
    settings = get_settings()
    llm = LLMClient(settings)
    notes: list[str] = []

    mode = "llm+search" if llm.available else "search+heuristic"
    queries: list[str] = []
    candidates = []

    if seed_only:
        candidates = seed_candidates_for(req.product, req.country)
        queries = plan_queries(req.product, req.country, llm=None)
        mode = "seed_only"
        notes.append(
            "Ran in seed_only mode for deterministic high-precision sample output."
        )
    else:
        candidates, queries = discover_candidates(req.product, req.country, llm=llm)
        seed = seed_candidates_for(req.product, req.country) if use_seed_fallback else []
        if seed:
            search_hits = candidates
            candidates = list(seed)
            by_site = {
                (c.website or c.source_url or c.name).rstrip("/").lower(): c
                for c in candidates
            }
            added_search = 0
            for s in search_hits:
                key = (s.website or s.source_url or s.name).rstrip("/").lower()
                if key not in by_site:
                    candidates.append(s)
                    by_site[key] = s
                    added_search += 1
            notes.append(
                f"Blended {len(seed)} curated public companies with {added_search} "
                "search hits. Curated companies are enriched first for precision."
            )
            mode = mode + "+seed_blend"

    if not candidates:
        notes.append(
            "No candidates found. Check network access or try a broader product term."
        )
        return DiscoveryResult(
            product=req.product,
            country=req.country,
            top_n=req.top_n,
            generated_at=datetime.now(timezone.utc).isoformat(),
            mode=mode,
            queries_used=queries,
            importers=[],
            notes=notes,
        )

    enriched = enrich_many(candidates, settings)
    ranked = rank_importers(
        req.product,
        req.country,
        enriched,
        top_n=req.top_n,
        llm=llm if llm.available and not seed_only else None,
    )

    if not llm.available and not seed_only:
        notes.append(
            "No LLM API key set. Ranking used transparent heuristic scores only. "
            "Add OPENAI_API_KEY or GEMINI_API_KEY for stronger extraction."
        )

    notes.append(
        "Contact fields are taken from public website text when available. "
        "Missing email/phone usually means the site hides them behind forms."
    )

    return DiscoveryResult(
        product=req.product,
        country=req.country,
        top_n=req.top_n,
        generated_at=datetime.now(timezone.utc).isoformat(),
        mode=mode,
        queries_used=queries,
        importers=ranked,
        notes=notes,
    )
