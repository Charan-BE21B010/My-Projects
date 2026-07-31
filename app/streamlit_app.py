from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_engine.models import DiscoveryRequest
from importer_engine.pipeline import run_discovery

st.set_page_config(
    page_title="Importer Discovery Engine",
    page_icon="🔎",
    layout="wide",
)

st.title("Importer Discovery Engine")
st.caption(
    "Find and rank relevant importer companies for an Indian exporter "
    "entering a foreign market."
)

with st.sidebar:
    st.header("Query")
    product = st.text_input("Product", value="Ceramic Tiles")
    country = st.text_input("Target country", value="Germany")
    top_n = st.slider("Top N", 3, 15, 8)
    context = st.text_area(
        "Exporter context (optional)",
        placeholder="e.g. Morbi-based ceramic maker, ISO certified, 2 containers/month",
    )
    run = st.button("Discover importers", type="primary")

    st.divider()
    st.markdown("**Sample presets**")
    if st.button("Ceramic Tiles / Germany"):
        st.session_state["preset"] = ("Ceramic Tiles", "Germany")
    if st.button("Basmati Rice / UAE"):
        st.session_state["preset"] = ("Basmati Rice", "UAE")
    if st.button("Cotton Textiles / USA"):
        st.session_state["preset"] = ("Cotton Textiles", "USA")

if "preset" in st.session_state:
    product, country = st.session_state.pop("preset")
    st.rerun()

if run:
    with st.spinner("Searching, enriching and ranking..."):
        result = run_discovery(
            DiscoveryRequest(
                product=product,
                country=country,
                top_n=top_n,
                exporter_context=context or None,
            )
        )
    st.session_state["result"] = result

result = st.session_state.get("result")
if result:
    st.subheader(f"Results for {result.product} -> {result.country}")
    st.write(f"Mode: `{result.mode}` | Generated: {result.generated_at}")

    for row in result.importers:
        with st.container(border=True):
            cols = st.columns([3, 1])
            cols[0].markdown(f"### {row.rank}. {row.company_name}")
            cols[1].metric("Relevance", f"{row.relevance_score:.0f}")
            st.write(row.match_reason)
            m1, m2, m3, m4 = st.columns(4)
            m1.write(f"**Website:** {row.website or 'n/a'}")
            m2.write(f"**Email:** {row.contact_email or 'n/a'}")
            m3.write(f"**Phone:** {row.contact_phone or 'n/a'}")
            m4.write(f"**LinkedIn:** {row.contact_linkedin or 'n/a'}")
            with st.expander("Score breakdown & sources"):
                st.json(
                    {
                        "confidence": row.confidence,
                        "score_breakdown": row.score_breakdown,
                        "sources_used": row.sources_used,
                    }
                )

    for note in result.notes:
        st.info(note)

    st.download_button(
        "Download JSON",
        data=result.model_dump_json(indent=2),
        file_name=f"{result.product}_{result.country}.json".replace(" ", "_").lower(),
        mime="application/json",
    )

    sample_path = ROOT / "samples"
    st.divider()
    st.markdown("### Bundled sample outputs")
    for path in sorted(sample_path.glob("*.json")):
        with st.expander(path.name):
            st.json(json.loads(path.read_text(encoding="utf-8")))
else:
    st.markdown(
        """
        Enter a product and country, then hit **Discover importers**.

        The pipeline:
        1. builds search queries
        2. discovers candidate companies from the public web
        3. enriches contact details from company sites
        4. ranks by product fit, geography, importer role, and contactability
        """
    )