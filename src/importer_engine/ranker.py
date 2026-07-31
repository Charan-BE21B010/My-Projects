from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

from importer_engine.llm import LLMClient
from importer_engine.models import ContactInfo, RankedImporter, RawCandidate


ROLE_PATTERNS = [
    (r"\b(importer|importing|imports)\b", 22),
    (r"\b(distributor|distribution)\b", 16),
    (r"\b(wholesale|wholesaler|großhandel|grosshandel)\b", 16),
    (r"\b(trading company|trader|handel)\b", 10),
    (r"\b(buyer|procurement|einkauf)\b", 12),
]

NEGATIVE_PATTERNS = [
    (r"\b(manufacturer only|we manufacture|our factory)\b", -8),
    (r"\b(job|hiring|vacancy|career)\b", -15),
    (r"\b(news|press release)\b", -10),
]

JUNK_NAME = re.compile(
    r"(top\s+\d+|best\s+\d+|dealer in moscow|dealer in russia|"
    r"buyers?\s*&\s*importers|import data|trade lead|directory|"
    r"pdf\)|consumption of electric)",
    re.I,
)


def _token_overlap(a: str, b: str) -> float:
    wa = {w for w in re.findall(r"[a-z0-9]+", a.lower()) if len(w) > 2}
    wb = {w for w in re.findall(r"[a-z0-9]+", b.lower()) if len(w) > 2}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa)


def _host(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def heuristic_score(
    product: str,
    country: str,
    candidate: RawCandidate,
    contact: ContactInfo,
) -> tuple[float, dict[str, float], str]:
    blob = f"{candidate.name} {candidate.snippet} {candidate.website or ''}".lower()
    breakdown: dict[str, float] = {}

    # Seed snippets are curated; give them a fair base product score
    base = 18.0 if candidate.source_label == "seed" else 10.0
    product_fit = min(28.0, base + _token_overlap(product, blob) * 30.0)
    # synonym boosts for tiles / spices / textiles
    pl = product.lower()
    if any(k in pl for k in ["tile", "ceramic", "fliesen"]) and any(
        k in blob for k in ["tile", "fliesen", "keramik", "ceramic", "porcelain"]
    ):
        product_fit = max(product_fit, 24.0)
    if any(k in pl for k in ["spice", "rice", "basmati"]) and any(
        k in blob for k in ["spice", "rice", "basmati", "food", "commodity", "agro"]
    ):
        product_fit = max(product_fit, 24.0)
    if any(k in pl for k in ["textile", "cotton", "apparel", "fabric"]) and any(
        k in blob for k in ["textile", "fabric", "cotton", "apparel", "garment"]
    ):
        product_fit = max(product_fit, 24.0)
    breakdown["product_fit"] = round(product_fit, 1)

    country_l = country.lower()
    geo = 0.0
    host = _host(candidate.website or candidate.source_url or "")
    geo_map = {
        "germany": ["deutschland", ".de", "german"],
        "uae": ["dubai", "abu dhabi", "emirates", ".ae"],
        "united arab emirates": ["dubai", "abu dhabi", "emirates", ".ae"],
        "usa": ["united states", ".us", "america"],
        "united states": ["usa", "united states", ".us"],
    }
    cues = geo_map.get(country_l, [country_l])
    if country_l in blob or any(x in blob for x in cues):
        geo = 18.0
    elif host.endswith((".de", ".ae", ".us", ".uk", ".fr", ".nl", ".sa", ".com")):
        # local TLD boost
        if country_l in {"germany", "deutschland"} and host.endswith(".de"):
            geo = 18.0
        elif country_l in {"uae", "united arab emirates", "dubai"} and host.endswith(".ae"):
            geo = 18.0
        elif country_l in {"usa", "united states", "us"} and (
            host.endswith(".us") or ".com" in host
        ):
            # weak for .com; only if USA cues already missed
            geo = 10.0 if candidate.source_label == "seed" else 6.0
    breakdown["geo_fit"] = geo

    role = 0.0
    for pat, pts in ROLE_PATTERNS:
        if re.search(pat, blob, re.I):
            role = max(role, float(pts))
    for pat, pts in NEGATIVE_PATTERNS:
        if re.search(pat, blob, re.I):
            role += pts
    if candidate.source_label == "seed":
        role = max(role, 18.0)
    role = max(0.0, min(22.0, role))
    breakdown["importer_role"] = role

    contact_score = 0.0
    if contact.email:
        contact_score += 12.0
    if contact.phone:
        contact_score += 8.0
    if contact.linkedin:
        contact_score += 5.0
    if candidate.website:
        contact_score += 5.0
    breakdown["contactability"] = min(30.0, contact_score)

    evidence = 8.0 if candidate.source_url else 0.0
    if candidate.snippet and len(candidate.snippet) > 80:
        evidence += 4.0
    breakdown["evidence"] = min(12.0, evidence)

    total = sum(breakdown.values())
    total = max(0.0, min(100.0, total))

    reason_bits = []
    if breakdown["product_fit"] >= 18:
        reason_bits.append(f"product keywords align with {product}")
    if breakdown["geo_fit"] >= 12:
        reason_bits.append(f"clear footprint in {country}")
    if breakdown["importer_role"] >= 14:
        reason_bits.append("signals importer/distributor/wholesale role")
    if contact.email or contact.phone:
        reason_bits.append("public contact details found")
    if not reason_bits:
        reason_bits.append("weak but possible match from public search")

    return round(total, 1), breakdown, "; ".join(reason_bits)


def llm_rerank(
    product: str,
    country: str,
    rows: list[tuple[RawCandidate, ContactInfo, list[str], float, dict, str]],
    llm: LLMClient,
) -> list[tuple[RawCandidate, ContactInfo, list[str], float, dict, str]]:
    payload = []
    for i, (cand, contact, sources, score, breakdown, reason) in enumerate(rows):
        payload.append(
            {
                "id": i,
                "name": cand.name,
                "website": cand.website,
                "snippet": cand.snippet[:280],
                "heuristic_score": score,
                "email": contact.email,
                "phone": contact.phone,
            }
        )
    try:
        data = llm.complete_json(
            system=(
                "You are ranking importer leads for an Indian exporter. "
                "Prefer genuine importers/distributors over retailers or "
                "unrelated firms. Adjust scores 0-100 and write a short "
                "match_reason. Return JSON: "
                '{"rankings":[{"id":0,"relevance_score":0,"match_reason":""}]}'
            ),
            user=f"Product: {product}\nCountry: {country}\nCandidates: {payload}",
        )
        by_id = {int(r["id"]): r for r in data.get("rankings", []) if "id" in r}
        updated = []
        for i, row in enumerate(rows):
            cand, contact, sources, score, breakdown, reason = row
            if i in by_id:
                adj = float(by_id[i].get("relevance_score", score))
                final = round(0.55 * score + 0.45 * adj, 1)
                final = max(0.0, min(100.0, final))
                reason = by_id[i].get("match_reason") or reason
                breakdown = {**breakdown, "llm_adjusted": adj}
                updated.append((cand, contact, sources, final, breakdown, reason))
            else:
                updated.append(row)
        updated.sort(key=lambda x: x[3], reverse=True)
        return updated
    except Exception:
        return rows


def rank_importers(
    product: str,
    country: str,
    enriched: list[tuple[RawCandidate, ContactInfo, list[str]]],
    top_n: int = 8,
    llm: Optional[LLMClient] = None,
) -> list[RankedImporter]:
    scored = []
    country_l = country.strip().lower()

    for cand, contact, sources in enriched:
        score, breakdown, reason = heuristic_score(product, country, cand, contact)
        is_seed = cand.source_label == "seed"

        if breakdown.get("product_fit", 0) < 14 and breakdown.get("importer_role", 0) < 8:
            continue
        if breakdown.get("product_fit", 0) < 16 and breakdown.get("contactability", 0) >= 25:
            score = min(score, 48.0)
        if re.fullmatch(
            r"(germany|usa|uae|india|home|welcome|index|about|contact)",
            cand.name.strip(),
            flags=re.I,
        ):
            continue
        if JUNK_NAME.search(cand.name):
            continue

        site = (cand.website or "").lower()
        host = _host(site)
        if country_l not in {"india"} and (site.endswith(".in") or host.endswith(".in")):
            continue
        # drop wrong-geography noise for non-seed hits
        if not is_seed and breakdown.get("geo_fit", 0) < 8:
            continue
        if not is_seed and breakdown.get("importer_role", 0) < 10:
            continue
        # Russia / China / random markets when asking for DE/UAE/USA
        wrong_geo = ("russia", "moscow", "china", "pakistan", "bangladesh")
        if not is_seed and any(w in cand.name.lower() or w in (cand.snippet or "").lower() for w in wrong_geo):
            if country_l not in wrong_geo:
                continue

        scored.append((cand, contact, sources, score, breakdown, reason))

    # Prefer seeds when scores are close
    scored.sort(
        key=lambda x: (x[3], 1 if x[0].source_label == "seed" else 0),
        reverse=True,
    )
    scored = scored[: max(top_n * 2, top_n)]

    if llm and llm.available and scored:
        scored = llm_rerank(product, country, scored, llm)

    scored = scored[:top_n]
    results: list[RankedImporter] = []
    for i, (cand, contact, sources, score, breakdown, reason) in enumerate(scored, start=1):
        confidence = "high" if score >= 70 else "medium" if score >= 45 else "low"
        results.append(
            RankedImporter(
                rank=i,
                company_name=cand.name,
                website=cand.website,
                relevance_score=score,
                match_reason=reason,
                contact_email=contact.email,
                contact_phone=contact.phone,
                contact_linkedin=contact.linkedin,
                sources_used=sources[:6],
                score_breakdown=breakdown,
                confidence=confidence,
            )
        )
    return results
