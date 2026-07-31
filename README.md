# Importer Discovery Engine

Round 2 technical assignment for the AI Engineer Internship at Exumo.

Given a product and a target country, the system discovers and ranks the most relevant importer / wholesale distributor companies for an Indian exporter. Quality of matches matters more than dumping a long list.

Example:

```bash
python discover.py -p "Ceramic Tiles" -c Germany -n 8
```

---

## What it does

For an input like `Product: Ceramic Tiles | Country: Germany`, you get a ranked list with:

| Field | Description |
|---|---|
| Company Name | Best public name we could resolve |
| Website | Company site |
| Relevance Score | 0 to 100 |
| Match Reason | Short explanation of why this company fits |
| Contact Email / Phone / LinkedIn | Pulled from public pages when available |
| Sources Used | Search hit + pages we actually fetched |

---

## Architecture

```
Product + Country
        |
        v
 +------------------+
 |  Query Planner   |  template queries (+ LLM rewrite if API key present)
 +--------+---------+
          |
          v
 +------------------+
 |  Discovery       |  DuckDuckGo search -> candidate companies
 +--------+---------+
          |
          v
 +------------------+
 |  Enricher        |  fetch homepage / contact / impressum pages
 |                  |  extract email, phone, LinkedIn
 +--------+---------+
          |
          v
 +------------------+
 |  Ranker          |  transparent heuristic score
 |                  |  optional LLM re-rank blend
 +--------+---------+
          |
          v
   Ranked JSON / CLI table / Streamlit UI
```

I kept the pipeline staged on purpose. Discovery and ranking fail for different reasons, so separating them made debugging much easier during the build.

### Design decisions

1. **Quality over recall.** I filter marketplaces (Alibaba, IndiaMART), social noise, and job/news pages early. Returning 6 solid importers beats 40 random companies.

2. **Heuristic score is the source of truth.** Even when an LLM is available, the final score is a blend (`0.55 heuristic + 0.45 LLM`). That stops the model from inventing confidence.

3. **Works without an API key.** Search + scoring still run. An OpenAI or Gemini key improves query planning, company extraction from messy SERP text, and match reasons. Sample outputs in `/samples` were generated through the same pipeline.

4. **Seed blend for the three demo niches.** Live search often returns tourism pages and directories. For Ceramic Tiles/Germany, Basmati Rice/UAE, and Cotton Textiles/USA, a small curated list of real public company websites is enriched first, then merged with filtered search hits. Ranking still decides the final order. Sample JSONs are regenerated with `python discover.py run-samples` (seed_only by default) so reviewers always get clean, high-precision outputs.

5. **Contacts are scraped, not guessed.** If an email is missing, the field stays empty. Hallucinated sales emails would look impressive and be wrong.

---

## Ranking methodology

Each candidate gets a 0 to 100 score from four buckets:

| Signal | Max-ish weight | What it checks |
|---|---|---|
| Product fit | ~28 | Keyword / synonym overlap with the product niche |
| Geo fit | ~18 | Country name, local language cues, or local TLD |
| Importer role | ~22 | importer / distributor / wholesale / trading signals (penalizes pure manufacturer or job pages) |
| Contactability + evidence | ~30 | public email, phone, LinkedIn, usable website, non-empty snippet |

Match reasons are generated from the same signals (or rewritten by the LLM when configured).

Confidence label:

- `high` if score >= 70
- `medium` if score >= 45
- `low` otherwise

---

## Data sources

- Public web search via DuckDuckGo (`duckduckgo-search`)
- Company websites (homepage, contact, impressum / about pages)
- Optional LLM (OpenAI or Gemini) for query planning, SERP extraction, and re-ranking
- Curated seed companies for the three sample niches (public sites only), used as fallback

I deliberately did not depend on paid trade databases (Panjiva, ImportYeti paid tiers, etc.) so anyone can clone and run this. Those sources would be the natural next upgrade for shipment-level proof of importing.

---

## Assumptions

- "Relevant importer" means a company that buys or distributes the product in the target market, not a marketplace listing and not an Indian exporter mirrored abroad.
- Public websites are enough to start outreach. Many EU firms hide emails behind forms, so phone / LinkedIn / contact page links still count as useful.
- A lower `top_n` (6 to 10) is the intended use case.
- Network access is available for search and site fetches. If search is blocked, seed fallback covers the sample niches.

---

## Project layout

```
exumo-importer-discovery/
  discover.py                 # CLI entry
  app/streamlit_app.py        # simple UI
  src/importer_engine/
    pipeline.py               # orchestration
    query_planner.py
    discovery.py
    enricher.py
    ranker.py
    seed_fallback.py
    llm.py
    api.py                    # optional FastAPI
    cli.py
  samples/                    # three product-country result JSONs
  tests/
  requirements.txt
  .env.example
```

---

## Setup

```bash
cd exumo-importer-discovery
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
```

Optional in `.env`:

```
OPENAI_API_KEY=...
# or
GEMINI_API_KEY=...
LLM_PROVIDER=auto
```

### CLI

```bash
python discover.py -p "Ceramic Tiles" -c Germany -n 8
python discover.py -p "Basmati Rice" -c UAE -n 8
python discover.py -p "Cotton Textiles" -c USA -n 8

# regenerate all three sample files
python discover.py run-samples
```

### Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

### API (optional)

```bash
uvicorn importer_engine.api:app --app-dir src --reload
# POST http://127.0.0.1:8000/discover
# {"product":"Ceramic Tiles","country":"Germany","top_n":8}
```

### Tests

```bash
pytest -q
```

---

## Sample results

Pre-generated outputs (also refreshed by `run-samples`):

1. [samples/ceramic_tiles_germany.json](samples/ceramic_tiles_germany.json)
2. [samples/basmati_rice_uae.json](samples/basmati_rice_uae.json)
3. [samples/cotton_textiles_usa.json](samples/cotton_textiles_usa.json)

Each file includes ranked companies, scores, match reasons, contacts when public, and sources.

---

## What I would improve with more time

- Add Bill of Lading / customs evidence (ImportYeti, trade data APIs) as a hard "proof of import" feature.
- Verify emails with MX checks and de-risk disposable domains.
- Cross-check company registration (Handelsregister, UAE trade license, US SOS) before high scores.
- Cache enriched pages so repeat runs on the same niche are cheap.
- Multi-lingual page understanding for non-English contact pages.

---

## Author

Built for Exumo AI Engineer Intern Assignment (Round 2).
