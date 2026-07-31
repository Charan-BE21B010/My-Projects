"""
Curated seed candidates used for demo niches and as a precision blend with search.
These are real public companies. known_* fields are public contacts observed earlier.
"""

from __future__ import annotations

from importer_engine.models import RawCandidate


SEEDS: dict[str, list[RawCandidate]] = {
    "ceramic tiles|germany": [
        RawCandidate(
            name="Welscheit Import Export GmbH",
            website="https://www.welscheit.de/en",
            snippet=(
                "Mosaic and ceramic import/export since 1962. Europe-wide mosaic "
                "wholesale for commercial customers in Germany."
            ),
            source_url="https://www.welscheit.de/en",
            source_label="seed",
            known_email="info@welscheit.de",
            known_phone="+49 (0)2508 678959-0",
        ),
        RawCandidate(
            name="Fliesen-Zentrum Deutschland GmbH",
            website="https://www.fliesen-zentrum.de/",
            snippet=(
                "German tile specialist with wholesale centers and showrooms. "
                "Focus on ceramic tiles, building materials and flooring for pros."
            ),
            source_url="https://www.fliesen-zentrum.de/",
            source_label="seed",
            known_email="onlineberatung@fliesen-zentrum.de",
            known_phone="+49 30 3435599-0",
        ),
        RawCandidate(
            name="KERAMUNDO",
            website="https://www.keramundo.de/",
            snippet=(
                "Large Fliesenfachhandel network in Germany with many locations "
                "and broad ceramic tile assortments from international makers."
            ),
            source_url="https://www.keramundo.de/",
            source_label="seed",
            known_email="info@stark-deutschland.de",
            known_phone="+49 69 668110-0",
        ),
        RawCandidate(
            name="CERANDO",
            website="https://cerando.de/",
            snippet=(
                "Direct distribution of Spanish and Italian porcelain and ceramic "
                "tiles in NRW, Germany. B2B oriented tile assortment."
            ),
            source_url="https://cerando.de/",
            source_label="seed",
            known_email="info@cerando.de",
            known_phone="+49 (0)2381 9143035",
        ),
        RawCandidate(
            name="Rheinimex GmbH",
            website="https://rheinimex.de/",
            snippet=(
                "NRW-based firm highlighting import of ceramic and porcelain tiles "
                "for residential and industrial projects in Germany."
            ),
            source_url="https://rheinimex.de/",
            source_label="seed",
            known_email="info@rheinimex.de",
            known_phone="+49 2173 2600547",
        ),
        RawCandidate(
            name="Agrob Buchtal",
            website="https://agrob-buchtal.de/",
            snippet=(
                "Major German ceramics group supplying architectural ceramic tiles "
                "and related systems across Germany and Europe."
            ),
            source_url="https://agrob-buchtal.de/",
            source_label="seed",
            known_email="agrob-buchtal@deutsche-steinzeug.de",
            known_phone="+49 9435 391 0",
        ),
    ],
    "basmati rice|uae": [
        RawCandidate(
            name="Dar Alshumukh General Trading L.L.C.",
            website="https://daralshumukh.com/",
            snippet=(
                "Dubai agro commodities firm partnered with Indian manufacturing "
                "for basmati rice, turmeric and dry red chillies."
            ),
            source_url="https://daralshumukh.com/",
            source_label="seed",
            known_email="sales@daralshumukh.com",
            known_linkedin="https://www.linkedin.com/in/nagaraju-vallepu-785659354/",
        ),
        RawCandidate(
            name="Five Oceans Trading L.L.C",
            website="https://www.fiveoceanstrading.com/",
            snippet=(
                "Dubai trading house (est. 1984) importing and wholesaling basmati "
                "and non-basmati rice, spices, pulses and sugar."
            ),
            source_url="https://www.fiveoceanstrading.com/",
            source_label="seed",
            known_email="info@fiveoceanstrading.com",
        ),
        RawCandidate(
            name="Fresh Harvest Trading",
            website="https://freshharvesttradingcollc.com/",
            snippet=(
                "ISO certified wholesale food distributor in UAE for bulk rice, "
                "sugar, spices and commodities serving HORECA and retail."
            ),
            source_url="https://freshharvesttradingcollc.com/",
            source_label="seed",
        ),
        RawCandidate(
            name="Orgaviya Foods",
            website="https://orgaviyafoods.com/",
            snippet=(
                "UAE B2B supplier of premium basmati rice, pulses and Indian spices "
                "bridging Indian farms to GCC buyers."
            ),
            source_url="https://orgaviyafoods.com/",
            source_label="seed",
        ),
        RawCandidate(
            name="Evergreen Delight Goods Wholesalers L.L.C.",
            website="https://www.evergreendgw.com/",
            snippet=(
                "Dubai Al Ras commodity trading house dealing basmati rice, spices "
                "and agro products for GCC and wider markets."
            ),
            source_url="https://www.evergreendgw.com/",
            source_label="seed",
            known_email="evergreen.dgw@gmail.com",
        ),
        RawCandidate(
            name="Al Saqar Trading",
            website="https://alsaqartrading.com/",
            snippet=(
                "UAE importer and trader of premium basmati rice with long-standing "
                "wholesale distribution across the Emirates."
            ),
            source_url="https://alsaqartrading.com/",
            source_label="seed",
            known_email="saqartrd@eim.ae",
            known_phone="+971 2 677 7792",
        ),
    ],
    "cotton textiles|usa": [
        RawCandidate(
            name="WearMax Inc",
            website="https://www.wearmaxinc.com/",
            snippet=(
                "USA wholesale textile importer/manufacturer of cotton and blended "
                "fabrics, sourcing from India, Pakistan, Bangladesh and more."
            ),
            source_url="https://www.wearmaxinc.com/",
            source_label="seed",
            known_phone="631-361-6388",
        ),
        RawCandidate(
            name="ENY Textiles, Inc.",
            website="https://enytextiles.net/",
            snippet=(
                "Los Angeles Fashion District importer and wholesaler of cotton and "
                "blended woven fabrics since 1984."
            ),
            source_url="https://enytextiles.net/",
            source_label="seed",
            known_email="ryoussefzadeh@enytextiles.net",
            known_phone="213-748-1400",
        ),
        RawCandidate(
            name="Impex Textile",
            website="https://www.impextextile.com/",
            snippet=(
                "US sourcing and converting company specializing in natural fabrics "
                "including cottons and linens for apparel brands."
            ),
            source_url="https://www.impextextile.com/",
            source_label="seed",
            known_phone="323-888-8500",
        ),
        RawCandidate(
            name="Tabb Textile Company Inc.",
            website="https://www.tabbtextileinc.com/",
            snippet=(
                "Alabama-based converter, importer and manufacturer of fabrics and "
                "finished textile goods for commercial and apparel markets."
            ),
            source_url="https://www.tabbtextileinc.com/",
            source_label="seed",
            known_email="zach@textilegroup.net",
        ),
        RawCandidate(
            name="Go Textile",
            website="https://gotextileco.com/",
            snippet=(
                "Los Angeles knit fabric mill and importer supplying the US garment "
                "industry with domestic knits and imported materials."
            ),
            source_url="https://gotextileco.com/",
            source_label="seed",
            known_email="req@euphoriccolors.com",
            known_phone="800-775-7227",
        ),
        RawCandidate(
            name="Fox-Rich Textiles",
            website="https://fox-rich.com/",
            snippet=(
                "US textile company supplying fabrics to apparel and commercial "
                "buyers, including imported cotton and blended materials."
            ),
            source_url="https://fox-rich.com/",
            source_label="seed",
        ),
    ],
}


ALIASES = {
    "ceramic tiles|germany": [
        "ceramic tiles|germany",
        "ceramic tile|germany",
        "tiles|germany",
        "fliesen|germany",
        "porcelain tiles|germany",
    ],
    "basmati rice|uae": [
        "basmati rice|uae",
        "basmati rice|united arab emirates",
        "basmati rice|dubai",
        "spices|uae",
        "rice|uae",
        "rice and spices|uae",
    ],
    "cotton textiles|usa": [
        "cotton textiles|usa",
        "cotton textiles|united states",
        "cotton fabric|usa",
        "textiles|usa",
        "apparel textiles|usa",
        "cotton yarn|usa",
    ],
}


def _key(product: str, country: str) -> str:
    return f"{product.strip().lower()}|{country.strip().lower()}"


def seed_candidates_for(product: str, country: str) -> list[RawCandidate]:
    want = _key(product, country)
    for canon, aliases in ALIASES.items():
        if want in aliases or want == canon:
            return list(SEEDS[canon])
    for canon, rows in SEEDS.items():
        p, c = canon.split("|", 1)
        if c in want and any(tok in want for tok in p.split() if len(tok) > 3):
            return list(rows)
    return []
