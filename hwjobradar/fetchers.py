import hashlib
import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Job

UA = "Mozilla/5.0 (compatible; IsraelHWJobRadar/0.1; +https://github.com/)"
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
ISRAEL_HINTS = (
    "israel", "tel aviv", "tel-aviv", "herzliya", "haifa", "yokneam", "yokne'am",
    "raanana", "ra'anana", "petah tikva", "petah-tikva", "hod hasharon", "hod-hasharon",
    "jerusalem", "rehovot", "caesarea", "kiryat gat", "migdal haemek", "migdal ha'emek",
    "ness ziona", "nes ziona", "ramat gan", "beer sheva", "be'er sheva", "tel aviv-yafo",
    "modiin", "modi'in", "modi’in", "yehud", "kfar saba", "kfar sava", "netanya",
    "givataim", "givatayim", "rosh haayin", "rosh ha'ayin", "holon", "rishon lezion",
    "ashdod", "ness-ziona", "rehovot",
)


def _slug_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8", "ignore")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _looks_israel(text: str) -> bool:
    t = (text or "").lower()
    return any(x in t for x in ISRAEL_HINTS)


def fetch_workday(src: dict) -> list[Job]:
    tenant, dc, site = src["tenant"], src["dc"], src["site"]
    name = src.get("name", tenant)
    prefix = src.get("id_prefix", tenant)
    countries = [c.lower() for c in src.get("countries", ["Israel"])]
    url = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    base = f"https://{tenant}.{dc}.myworkdayjobs.com/en-US/{site}"
    sess = requests.Session(); sess.headers.update({**HEADERS, "Content-Type": "application/json"})

    def post(applied, offset=0, search_text=""):
        r = sess.post(url, json={"appliedFacets": applied, "limit": 20, "offset": offset, "searchText": search_text}, timeout=30)
        r.raise_for_status()
        if "json" not in r.headers.get("content-type", "").lower():
            raise RuntimeError("Workday returned non-JSON (possible temporary bot/rate limit block)")
        return r.json()

    first = post({}, 0, "")
    applied = {}
    facets = first.get("facets") or []
    for facet in facets:
        param = (facet.get("facetParameter") or "")
        if param not in ("locationCountry", "Location_Country", "country"):
            continue
        ids = []
        for v in facet.get("values") or []:
            desc = (v.get("descriptor") or "").strip().lower()
            if desc in countries or any(c in desc for c in countries):
                if v.get("id"): ids.append(v["id"])
        if ids:
            applied[param] = ids
            break

    # Country facet isn't always exposed. If absent, fetch globally and filter locally.
    jobs, seen = [], set()
    offset = 0
    while offset < src.get("max_results", 500):
        data = post(applied, offset, src.get("query", ""))
        rows = data.get("jobPostings") or []
        if not rows: break
        for row in rows:
            path = row.get("externalPath") or ""
            title = (row.get("title") or "").strip()
            loc = (row.get("locationsText") or row.get("primaryLocation") or "").strip()
            if not path or path in seen: continue
            seen.add(path)
            if not applied and not _looks_israel(loc):
                continue
            jobs.append(Job(
                id=f"{prefix}-{path.strip('/').split('/')[-1]}", title=title, company=name,
                location=loc, url=base + path, source=name,
            ))
        offset += len(rows)
        total = int(data.get("total") or 0)
        if total and offset >= total: break
        time.sleep(0.15)
    return jobs


def fetch_amazon(src: dict) -> list[Job]:
    name = src.get("name", "Amazon / Annapurna")
    prefix = src.get("id_prefix", "amazon")
    url = "https://www.amazon.jobs/en/search.json"
    jobs = []
    offset = 0
    while offset < src.get("max_results", 400):
        params = {
            "normalized_country_code[]": "ISR", "result_limit": 10, "offset": offset,
            "query": src.get("query", ""),
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=30); r.raise_for_status()
        data = r.json(); rows = data.get("jobs") or []
        if not rows: break
        for row in rows:
            jid = str(row.get("id_icims") or row.get("job_id") or row.get("id") or "")
            path = row.get("job_path") or ""
            jobs.append(Job(
                id=(f"{prefix}-{jid}" if jid else _slug_id(prefix, path)),
                title=(row.get("title") or "").strip(), company=name,
                location=(row.get("normalized_location") or row.get("location") or "").strip(),
                url=urljoin("https://www.amazon.jobs", path),
                posted=str(row.get("posted_date") or row.get("updated_at") or "")[:10],
                category=(row.get("business_category") or ""), source=name,
            ))
        offset += len(rows)
        if offset >= int(data.get("hits") or 0): break
        time.sleep(0.15)
    return jobs


def fetch_eightfold(src: dict) -> list[Job]:
    site = src["site"].rstrip("/")
    domain = src["domain"]
    name = src.get("name", domain)
    prefix = src.get("id_prefix", re.sub(r"\W+", "", name.lower()))
    countries = src.get("countries", ["Israel"])
    jobs = {}
    for country in countries:
        start = 0
        while start < src.get("max_results", 300):
            r = requests.get(
                site + "/api/pcsx/search", headers={**HEADERS, "Accept": "application/json"}, timeout=30,
                params={"domain": domain, "location": country, "start": start, "num": 10,
                        "sort_by": "timestamp", "filter_include_remote": 1},
            )
            r.raise_for_status(); data = (r.json().get("data") or {})
            rows = data.get("positions") or []
            if not rows: break
            for p in rows:
                raw_locs = " ".join(p.get("locations") or [])
                if country.lower() not in raw_locs.lower(): continue
                jid = str(p.get("displayJobId") or p.get("atsJobId") or p.get("id") or "")
                loc_parts = [x.strip() for x in (p.get("locations") or [""])[0].split(",") if x.strip() and x.strip().lower() != "multiple locations"]
                loc = ", ".join(loc_parts[1:] + loc_parts[:1]) if len(loc_parts) > 1 else raw_locs
                pos_url = p.get("positionUrl") or ""
                jobs[f"{prefix}-{jid}"] = Job(
                    id=f"{prefix}-{jid}", title=p.get("name", ""), company=name,
                    location=loc, url=urljoin(site, pos_url), category=(p.get("department") or ""),
                    posted="", source=name,
                )
            start += 10
            if start >= int(data.get("count") or 0): break
            time.sleep(0.15)
    return list(jobs.values())



def _in_countries(location: str, countries: list[str]) -> bool:
    if not countries:
        return True
    text = (location or "").lower()
    return any(c.strip().lower() in text for c in countries)


def fetch_greenhouse(src: dict) -> list[Job]:
    company = src["company"]
    name = src.get("name", company)
    countries = src.get("countries", ["Israel"])
    r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs", headers=HEADERS, timeout=30)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        if not _in_countries(loc, countries):
            continue
        out.append(Job(id=f"gh-{company}-{j['id']}", title=j.get("title", ""), company=name,
                       location=loc, url=j.get("absolute_url", ""), source=name))
    return out


def fetch_lever(src: dict) -> list[Job]:
    company = src["company"]
    name = src.get("name", company)
    countries = src.get("countries", ["Israel"])
    r = requests.get(f"https://api.lever.co/v0/postings/{company}?mode=json", headers=HEADERS, timeout=30)
    r.raise_for_status()
    out = []
    for j in r.json():
        loc = (j.get("categories") or {}).get("location", "")
        if not _in_countries(loc, countries):
            continue
        out.append(Job(id=f"lv-{company}-{j['id']}", title=j.get("text", ""), company=name,
                       location=loc, url=j.get("hostedUrl", ""), source=name))
    return out


def fetch_ashby(src: dict) -> list[Job]:
    company = src["company"]
    name = src.get("name", company)
    countries = src.get("countries", ["Israel", "Tel Aviv", "Herzliya", "Haifa", "Yokneam", "Raanana", "Rehovot"])
    r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        loc = j.get("location", "")
        if not _in_countries(loc, countries):
            continue
        out.append(Job(id=f"ab-{company}-{j['id']}", title=j.get("title", ""), company=name,
                       location=loc, url=j.get("jobUrl", ""), source=name,
                       category=j.get("departmentName", ""), posted=str(j.get("publishedAt", ""))[:10]))
    return out


def fetch_apple(src: dict) -> list[Job]:
    """Apple's search page embeds structured search results in router hydration data."""
    name = src.get("name", "Apple")
    prefix = src.get("id_prefix", "apple")
    max_pages = int(src.get("max_pages", 12))
    jobs = {}
    for page in range(1, max_pages + 1):
        r = requests.get(
            "https://jobs.apple.com/en-il/search",
            params={"location": "israel-ISR", "page": page},
            headers=HEADERS, timeout=30,
        )
        r.raise_for_status()
        m = re.search(
            r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.+?)"\);\s*</script>',
            r.text, re.DOTALL,
        )
        if not m:
            # Site shape changed: fail loudly so source-health monitoring catches it.
            if page == 1:
                raise RuntimeError("Apple search hydration data not found; adapter likely needs update")
            break
        try:
            raw = bytes(m.group(1), "utf-8").decode("unicode_escape")
            data = json.loads(raw)
            search = data["loaderData"]["search"]
            rows = search.get("searchResults") or []
            total = int(search.get("totalRecords") or 0)
        except Exception as e:
            raise RuntimeError(f"Apple search parse failed: {e}") from e
        if not rows:
            break
        for row in rows:
            title = (row.get("postingTitle") or "").strip()
            locs = row.get("locations") or []
            loc_parts = []
            for loc in locs[:4]:
                if isinstance(loc, dict):
                    loc_parts.append(loc.get("name") or loc.get("countryName") or "")
            location = ", ".join(x for x in loc_parts if x) or "Israel"
            position_id = str(row.get("positionId") or row.get("id") or "")
            if not position_id:
                continue
            url = f"https://jobs.apple.com/en-il/details/{position_id}"
            jobs[f"{prefix}-{position_id}"] = Job(
                id=f"{prefix}-{position_id}", title=title, company=name,
                location=location, url=url, source=name,
            )
        if total and page * len(rows) >= total:
            break
        time.sleep(0.15)
    return list(jobs.values())

def _jobs_from_jsonld(html_text: str, page_url: str, name: str, prefix: str) -> list[Job]:
    soup = BeautifulSoup(html_text, "html.parser")
    out = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            obj = json.loads(tag.get_text(strip=True) or "{}")
        except Exception:
            continue
        stack = obj if isinstance(obj, list) else [obj]
        for item in stack:
            if not isinstance(item, dict) or item.get("@type") != "JobPosting": continue
            title = item.get("title") or ""
            url = item.get("url") or page_url
            loc = ""
            jl = item.get("jobLocation") or {}
            if isinstance(jl, list): jl = jl[0] if jl else {}
            if isinstance(jl, dict):
                addr = jl.get("address") or {}
                if isinstance(addr, dict):
                    loc = ", ".join(str(addr.get(k) or "") for k in ("addressLocality", "addressRegion", "addressCountry") if addr.get(k))
            ident = item.get("identifier")
            if isinstance(ident, dict): ident = ident.get("value")
            jid = str(ident or url)
            out.append(Job(
                id=f"{prefix}-{jid}" if len(jid) < 100 else _slug_id(prefix, jid),
                title=title, company=name, location=loc, url=url,
                posted=str(item.get("datePosted") or "")[:10], category=str(item.get("occupationalCategory") or ""), source=name,
            ))
    return out


def fetch_html(src: dict) -> list[Job]:
    name = src["name"]
    prefix = src.get("id_prefix", re.sub(r"\W+", "", name.lower()))
    pages = src.get("urls") or [src["url"]]
    selector = src.get("item_selector", "a[href]")
    href_re = re.compile(src.get("href_regex", r"job|career|position|opening"), re.I)
    exclude_re = re.compile(src.get("href_exclude_regex", r"login|privacy|terms|benefits|life-at|locations?$"), re.I)
    by_url = {}

    for page in pages:
        r = requests.get(page, headers=HEADERS, timeout=30)
        r.raise_for_status()
        for j in _jobs_from_jsonld(r.text, page, name, prefix):
            by_url[j.url] = j
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select(selector):
            href = (a.get("href") or "").strip()
            if not href or exclude_re.search(href) or not href_re.search(href):
                continue
            full = urljoin(src.get("base_url", page), href)
            title = " ".join(a.stripped_strings).strip()
            if not title or len(title) < 3 or len(title) > 180:
                continue
            if not re.search(r"student|intern|graduate|engineer|design|verification|validation|firmware|embedded|fpga|hardware|architect|developer|silicon|quantum|cad|vlsi|soc|asic|dft|emulation", title, re.I):
                continue

            context_re = src.get("required_context_regex")
            context_text = title
            if context_re:
                node = a
                contexts = []
                for _ in range(int(src.get("context_levels", 4))):
                    node = getattr(node, "parent", None)
                    if node is None:
                        break
                    txt = " ".join(getattr(node, "stripped_strings", [])).strip()
                    jobish_links = 0
                    try:
                        for other in node.find_all("a", href=True):
                            ohref = (other.get("href") or "").strip()
                            otitle = " ".join(other.stripped_strings).strip()
                            if href_re.search(ohref) and re.search(
                                r"student|intern|graduate|engineer|design|verification|validation|firmware|embedded|fpga|hardware|architect|developer|silicon|quantum|cad|vlsi|soc|asic|dft|emulation",
                                otitle, re.I
                            ):
                                jobish_links += 1
                    except Exception:
                        pass
                    if jobish_links > 1:
                        break
                    if txt and len(txt) <= 1200:
                        contexts.append(txt)
                context_text = " | ".join(contexts) or title
                if not re.search(context_re, context_text, re.I):
                    continue

            if full in by_url:
                continue
            by_url[full] = Job(
                id=_slug_id(prefix, full), title=title, company=name,
                location=src.get("default_location", "Israel"), url=full, source=name,
                description=context_text[:2500],
            )
        time.sleep(0.1)
    return list(by_url.values())

def enrich_job(job: Job, timeout: int = 20) -> tuple[Job, bool]:
    """Fetch the official job page. Returns (job, appears_open)."""
    try:
        r = requests.get(job.url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return job, False
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join(soup.stripped_strings)
        job.description = text[:40000]
        low = text.lower()
        closed = (
            "job is no longer available", "position is no longer available", "job has been filled",
            "no longer accepting applications", "this job is closed", "position has been closed",
        )
        if any(x in low for x in closed):
            return job, False
        if not job.location or job.location == "Israel":
            # Don't invent a city; retain Israel. The description is used for scoring/constraints.
            job.location = job.location or "Israel"
        return job, True
    except Exception:
        # A detail-page failure should not erase a job discovered from a healthy official listing feed.
        return job, True


FETCHERS = {
    "workday": fetch_workday,
    "amazon": fetch_amazon,
    "apple": fetch_apple,
    "eightfold": fetch_eightfold,
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "html": fetch_html,
}


def fetch_source(src: dict) -> list[Job]:
    kind = src["type"]
    if kind not in FETCHERS:
        raise ValueError(f"Unsupported source type: {kind}")
    return FETCHERS[kind](src)
