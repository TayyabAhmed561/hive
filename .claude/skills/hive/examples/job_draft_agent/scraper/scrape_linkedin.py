import re
import requests
import time
from normalize import normalize


LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
LINKEDIN_JOB_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

SEARCH_QUERIES = [
    "machine learning intern",
    "ml intern",
    "ai research intern",
    "deep learning intern",
    "nlp intern",
    "computer vision intern",
    "data science intern",
    "machine learning co-op",
    "ml co-op",
    "research intern machine learning",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _extract_job_ids(html: str) -> list[str]:
    ids = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', html)
    if ids:
        return ids
    return re.findall(r'/jobs/view/(\d+)', html)


def _extract_titles(html: str) -> list[str]:
    titles = re.findall(r'class="sr-only">\s*\n?\s*(.*?)\s*\n?\s*<', html)
    if not titles:
        titles = re.findall(r'base-search-card__title[^>]*>\s*(.*?)\s*</', html)
    return [t.strip() for t in titles if t.strip()]


def _extract_companies(html: str) -> list[str]:
    companies = re.findall(
        r'base-search-card__subtitle[^>]*>.*?<a[^>]*>\s*(.*?)\s*</',
        html, re.DOTALL,
    )
    if not companies:
        companies = re.findall(r'hidden-nested-link[^>]*>\s*(.*?)\s*</', html)
    return [c.strip() for c in companies if c.strip()]


def _extract_locations(html: str) -> list[str]:
    raw = re.findall(r'job-search-card__location[^>]*>\s*(.*?)\s*</', html)
    return [loc.strip() for loc in raw if loc.strip()]


def _fetch_job_detail(job_id: str) -> str:
    try:
        resp = requests.get(
            LINKEDIN_JOB_URL.format(job_id=job_id),
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:3000]
    except Exception:
        pass
    return ""


def _scrape_query(query: str, params: dict, seen_ids: set) -> list[dict]:
    jobs = []
    try:
        resp = requests.get(
            LINKEDIN_SEARCH_URL,
            headers=HEADERS,
            params={**params, "keywords": query},
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        html = resp.text
        job_ids = _extract_job_ids(html)
        titles = _extract_titles(html)
        companies = _extract_companies(html)
        locations = _extract_locations(html)

        for i, job_id in enumerate(job_ids):
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = titles[i] if i < len(titles) else query
            company = companies[i] if i < len(companies) else ""
            location = locations[i] if i < len(locations) else "Canada"

            title = title.replace("&amp;", "&").replace("&#39;", "'").strip()
            company = company.replace("&amp;", "&").strip()

            if not company:
                continue

            description = _fetch_job_detail(job_id)
            time.sleep(0.5)

            job = normalize(
                company=company,
                title=title,
                location=location,
                description=description or title,
                url=f"https://www.linkedin.com/jobs/view/{job_id}",
                source="linkedin",
            )
            if job:
                jobs.append(job)

        time.sleep(1)

    except Exception as e:
        print(f"[LinkedIn] Failed for '{query}': {e}")

    return jobs


def scrape_linkedin() -> list[dict]:
    jobs = []
    seen_ids: set = set()

    canada_params = {
        "location": "Canada",
        "geoId": "101174742",
        "f_TPR": "r604800",
        "f_E": "1",
        "start": 0,
        "count": 25,
    }

    remote_params = {
        "f_WT": "2",
        "f_TPR": "r604800",
        "f_E": "1",
        "start": 0,
        "count": 25,
    }

    for query in SEARCH_QUERIES:
        jobs += _scrape_query(query, canada_params, seen_ids)

    jobs += _scrape_query("machine learning intern", remote_params, seen_ids)
    jobs += _scrape_query("ml research intern", remote_params, seen_ids)

    print(f"[LinkedIn] Found {len(jobs)} relevant jobs")
    return jobs


if __name__ == "__main__":
    results = scrape_linkedin()
    for j in results[:10]:
        print(f"  {j['company']} | {j['title']} | {j['location']}")
