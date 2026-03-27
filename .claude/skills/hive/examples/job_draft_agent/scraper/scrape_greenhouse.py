import requests
from normalize import normalize

# Jobicy is a free job board API that aggregates remote jobs
# It indexes companies using Greenhouse, Lever, and others
# No auth required, searches by keyword across ALL companies
JOBICY_API = "https://jobicy.com/api/v2/remote-jobs"

# Also use The Muse API which is free and has good ML coverage
MUSE_API = "https://www.themuse.com/api/public/jobs"

SEARCH_QUERIES = [
    "machine learning intern",
    "ml intern",
    "ai research intern",
    "deep learning intern",
    "nlp intern",
    "computer vision intern",
    "data science intern",
    "machine learning co-op",
    "research intern ai",
    "llm intern",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _scrape_jobicy() -> list[dict]:
    jobs = []
    seen_ids = set()

    for query in SEARCH_QUERIES:
        try:
            resp = requests.get(
                JOBICY_API,
                headers=HEADERS,
                params={
                    "search": query,
                    "count": 50,
                    "geo": "canada",
                },
                timeout=15,
            )
            if resp.status_code != 200:
                # Try without geo filter (catches remote)
                resp = requests.get(
                    JOBICY_API,
                    headers=HEADERS,
                    params={"search": query, "count": 50},
                    timeout=15,
                )

            if resp.status_code != 200:
                continue

            data = resp.json()
            postings = data.get("jobs", [])

            for hit in postings:
                job_id = str(hit.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                company = hit.get("companyName", "") or hit.get("company", "")
                title = hit.get("jobTitle", "") or hit.get("title", "")
                location = hit.get("jobGeo", "") or hit.get("location", "Remote")
                description = hit.get("jobDescription", "") or hit.get("description", "")
                url = hit.get("url", "") or hit.get("jobExcerpt", "")

                job = normalize(
                    company=company,
                    title=title,
                    location=location,
                    description=description,
                    url=url,
                    source="greenhouse",
                )
                if job:
                    jobs.append(job)

        except Exception as e:
            print(f"[Jobicy] Failed for '{query}': {e}")

    return jobs


def _scrape_muse() -> list[dict]:
    jobs = []
    seen_ids = set()

    for query in SEARCH_QUERIES[:5]:  # limit to avoid rate limiting
        try:
            resp = requests.get(
                MUSE_API,
                headers=HEADERS,
                params={
                    "query": query,
                    "level": "Internship",
                    "page": 0,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            for hit in data.get("results", []):
                job_id = str(hit.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                company = (hit.get("company") or {}).get("name", "")
                title = hit.get("name", "")
                locations = hit.get("locations", [])
                location = locations[0].get("name", "Remote") if locations else "Remote"
                description = hit.get("contents", "")
                url = hit.get("refs", {}).get("landing_page", "")

                job = normalize(
                    company=company,
                    title=title,
                    location=location,
                    description=description,
                    url=url,
                    source="greenhouse",
                )
                if job:
                    jobs.append(job)

        except Exception as e:
            print(f"[Muse] Failed for '{query}': {e}")

    return jobs


def scrape_greenhouse() -> list[dict]:
    """
    Search for ML intern jobs across all companies using
    Jobicy and The Muse aggregator APIs.
    """
    jobs = []

    jobicy_jobs = _scrape_jobicy()
    jobs += jobicy_jobs

    muse_jobs = _scrape_muse()
    jobs += muse_jobs

    print(f"[Greenhouse/Aggregators] Found {len(jobs)} relevant jobs "
          f"(Jobicy: {len(jobicy_jobs)}, Muse: {len(muse_jobs)})")
    return jobs


if __name__ == "__main__":
    results = scrape_greenhouse()
    for j in results[:10]:
        print(f"  {j['company']} | {j['title']} | {j['location']}")
