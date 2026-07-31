from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from importer_engine.models import ContactInfo, RawCandidate
from importer_engine.pipeline import run_discovery
from importer_engine.models import DiscoveryRequest
from importer_engine.ranker import heuristic_score, rank_importers
from importer_engine.seed_fallback import seed_candidates_for


def test_seed_germany_tiles():
    rows = seed_candidates_for("Ceramic Tiles", "Germany")
    assert len(rows) >= 4
    assert any("fliesen" in (r.name + (r.website or "")).lower() for r in rows)


def test_heuristic_prefers_importer_signal():
    cand = RawCandidate(
        name="NordTile Import GmbH",
        website="https://example-nordtile.de",
        snippet="German importer and wholesaler of ceramic tiles for contractors",
        source_url="https://example-nordtile.de",
    )
    contact = ContactInfo(email="sales@example-nordtile.de", phone="+49 123 4567890")
    score, breakdown, reason = heuristic_score("Ceramic Tiles", "Germany", cand, contact)
    assert score >= 55
    assert breakdown["importer_role"] > 0
    assert "tile" in reason.lower() or "product" in reason.lower()


def test_rank_orders_by_score():
    enriched = []
    for name, snippet, email in [
        (
            "Weak Co",
            "general trading company dealing in assorted goods",
            None,
        ),
        (
            "Strong Import",
            "importer and wholesale distributor of cotton textiles in USA",
            "buy@strong.com",
        ),
    ]:
        cand = RawCandidate(
            name=name,
            website=f"https://{name.replace(' ', '').lower()}.com",
            snippet=snippet,
            source_url=f"https://{name.replace(' ', '').lower()}.com",
            source_label="seed" if name.startswith("Strong") else "web_search",
        )
        enriched.append((cand, ContactInfo(email=email), [cand.source_url]))
    ranked = rank_importers("Cotton Textiles", "USA", enriched, top_n=2)
    assert ranked
    assert ranked[0].company_name == "Strong Import"


def test_seed_only_pipeline_no_crash():
    result = run_discovery(
        DiscoveryRequest(product="Ceramic Tiles", country="Germany", top_n=6),
        seed_only=True,
    )
    assert result.mode == "seed_only"
    assert len(result.importers) >= 4
    assert result.importers[0].company_name
    assert result.importers[0].relevance_score > 0
