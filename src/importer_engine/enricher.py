from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from importer_engine.config import Settings, get_settings
from importer_engine.models import ContactInfo, RawCandidate


EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}\b")
PHONE_RE = re.compile(
    r"(?:\+|00)?\d[\d\s().\-]{7,}\d"
)
LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9\-_%/]+",
    re.I,
)

SKIP_EMAIL_DOMAINS = {
    "example.com",
    "sentry.io",
    "wixpress.com",
    "schema.org",
    "googleapis.com",
    "cloudflare.com",
    "anthropic.com",
    "tradekey.com",
    "wix.com",
    "godaddy.com",
    "email.com",
    "domain.com",
    "sentry-next.wixpress.com",
}

PLACEHOLDER_LOCALS = {
    "your",
    "email",
    "name",
    "test",
    "user",
    "admin",
    "noreply",
    "no-reply",
}


def _clean_emails(emails: list[str]) -> list[str]:
    good = []
    for e in emails:
        e = e.strip().lower()
        domain = e.split("@")[-1]
        local = e.split("@")[0]
        if domain in SKIP_EMAIL_DOMAINS:
            continue
        if "sentry" in domain or domain.endswith(".wixpress.com"):
            continue
        if local in PLACEHOLDER_LOCALS or local.startswith("your"):
            continue
        if any(x in e for x in [".png", ".jpg", ".css", ".js"]):
            continue
        if len(local) >= 30 and all(c in "0123456789abcdef" for c in local):
            continue
        if e not in good:
            good.append(e)
    # prefer info/sales/contact/import/trade
    def rank(addr: str) -> int:
        local = addr.split("@")[0]
        for i, key in enumerate(
            ["import", "purchase", "procurement", "sales", "trade", "info", "contact", "hello"]
        ):
            if key in local:
                return i
        return 50

    return sorted(good, key=rank)


def _normalize_phone(raw: str) -> Optional[str]:
    raw = re.sub(r"\s+", " ", raw).strip()
    # reject dates, version-ish strings, and all-zero noise
    if re.match(r"^\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}$", raw):
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 8 or len(digits) > 15:
        return None
    if set(digits) <= {"0"}:
        return None
    # placeholder / sequential junk
    if digits in {"1234567890", "0123456789", "1111111111", "9999999999"}:
        return None
    if digits.startswith("123456"):
        return None
    # broken parenthesis patterns like "800) 775-7227"
    if raw.count("(") != raw.count(")"):
        return None
    # require some phone-like punctuation or leading + / country length
    if not re.search(r"[\+\(\)\-]", raw) and len(digits) < 10:
        return None
    return raw[:40]


def fetch_html(url: str, settings: Settings) -> Optional[str]:
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=settings.request_timeout_seconds,
            headers={"User-Agent": settings.user_agent},
        ) as client:
            r = client.get(url)
            if r.status_code >= 400:
                return None
            ctype = r.headers.get("content-type", "")
            if "text/html" not in ctype and "application/xhtml" not in ctype:
                return None
            return r.text
    except Exception:
        return None


def extract_contacts_from_html(html: str, base_url: str) -> ContactInfo:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    emails = _clean_emails(EMAIL_RE.findall(html) + EMAIL_RE.findall(text))
    phones = []
    for m in PHONE_RE.findall(text[:8000]):
        p = _normalize_phone(m)
        if p and p not in phones:
            phones.append(p)

    linkedins = LINKEDIN_RE.findall(html)
    # also from anchors
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com" in href.lower():
            full = urljoin(base_url, href)
            if LINKEDIN_RE.match(full) and full not in linkedins:
                linkedins.append(full)
        if href.lower().startswith("mailto:"):
            addr = href.split(":", 1)[1].split("?")[0]
            emails = _clean_emails(emails + [addr])
        if href.lower().startswith("tel:"):
            p = _normalize_phone(href.split(":", 1)[1])
            if p and p not in phones:
                phones.append(p)

    return ContactInfo(
        email=emails[0] if emails else None,
        phone=phones[0] if phones else None,
        linkedin=linkedins[0] if linkedins else None,
    )


def find_contact_pages(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    keys = ("contact", "kontakt", "about", "impressum", "imprint", "enquiry", "inquiry")
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        label = (a.get_text(" ", strip=True) or "").lower()
        low = href.lower()
        if any(k in low or k in label for k in keys):
            full = urljoin(base_url, href)
            if urlparse(full).scheme in {"http", "https"} and full not in urls:
                urls.append(full)
    return urls[:3]


def enrich_candidate(
    candidate: RawCandidate,
    settings: Optional[Settings] = None,
) -> tuple[RawCandidate, ContactInfo, list[str]]:
    """Fetch website (+ contact pages) and pull public contact fields."""
    settings = settings or get_settings()
    sources = [candidate.source_url] if candidate.source_url else []
    website = candidate.website or candidate.source_url
    contact = ContactInfo()

    if not website:
        contact.email = candidate.known_email
        contact.phone = candidate.known_phone
        contact.linkedin = candidate.known_linkedin
        return candidate, contact, sources

    html = fetch_html(website, settings)
    if not html:
        contact.email = candidate.known_email
        contact.phone = candidate.known_phone
        contact.linkedin = candidate.known_linkedin
        return candidate, contact, sources

    sources.append(website)
    contact = extract_contacts_from_html(html, website)

    # Prefer company name from <title> only when current name looks weak
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.string or "").strip() if soup.title else ""
    weak_name = (
        candidate.source_label != "seed"
        and (
            "." in candidate.name
            or candidate.name.lower() in {"unknown", "home", "index", "welcome"}
            or len(candidate.name) < 3
            or candidate.name.lower().startswith("www.")
        )
    )
    if title and weak_name:
        for sep in [" | ", " - ", " -- "]:
            if sep in title:
                candidate.name = title.split(sep)[0].strip()
                break
        else:
            if len(title) <= 80:
                candidate.name = title

    # deepen with contact pages if still missing fields
    if not (contact.email and contact.phone):
        for page in find_contact_pages(html, website):
            page_html = fetch_html(page, settings)
            if not page_html:
                continue
            sources.append(page)
            more = extract_contacts_from_html(page_html, page)
            contact.email = contact.email or more.email
            contact.phone = contact.phone or more.phone
            contact.linkedin = contact.linkedin or more.linkedin
            if contact.email and contact.phone:
                break

    # fall back to curated known contacts when page scrape misses them
    contact.email = contact.email or candidate.known_email
    contact.phone = contact.phone or candidate.known_phone
    contact.linkedin = contact.linkedin or candidate.known_linkedin

    # keep a bit of page text for ranking
    page_text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)[:1200]
    if page_text and len(page_text) > len(candidate.snippet):
        candidate.snippet = page_text[:400]

    return candidate, contact, list(dict.fromkeys(sources))


def enrich_many(
    candidates: list[RawCandidate],
    settings: Optional[Settings] = None,
) -> list[tuple[RawCandidate, ContactInfo, list[str]]]:
    settings = settings or get_settings()
    capped = candidates[: settings.max_enrich_requests]
    return [enrich_candidate(c, settings) for c in capped]