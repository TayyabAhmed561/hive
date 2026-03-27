import requests
from normalize import normalize

# Remotive is a free remote jobs API with no auth required
# It aggregates jobs from Lever, Greenhouse, and company sites
# Searchable by keyword across ALL companies
REMOTIVE_API = "https://remotive.com/api/remote-jobs"

# Also use Arbeitnow which has good coverage of European + remote ML jobs
ARBEITNOW_API = "https://www.arbeitnow.com/api/job-board-api"

SEARCH_CATEGORIES = [
    "software-dev",
    "data",
    "all",
]

ML_SEARCH_TERMS = [
    "machine learning intern",
    "ml intern",
    "ai intern",
    "deep learning intern",
    "nlp intern",
    "computer vision intern",
    "data science intern",
    "research intern",
    "machine learning co-op",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _scrape_remotive() -> list[dict]:
    jobs = []
    seen_ids = set()

    for term in ML_SEARCH_TERMS:
        try:
            resp = requests.get(
                REMOTIVE_API,
                headers=HEADERS,
                params={
                    "search": term,
                    "limit": 50,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            for hit in data.get("jobs", []):
                job_id = str(hit.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                company = hit.get("company_name", "")
                title = hit.get("title", "")
                location = hit.get("candidate_required_location", "Remote")
                description = hit.get("description", "")
                url = hit.get("url", "")

                job = normalize(
                    company=company,
                    title=title,
                    location=location,
                    description=description,
                    url=url,
                    source="lever",
                )
                if job:
                    jobs.append(job)

        except Exception as e:
            print(f"[Remotive] Failed for '{term}': {e}")

    return jobs


def _scrape_arbeitnow() -> list[dict]:
    """Arbeitnow aggregates remote + relocation jobs globally."""
    jobs = []
    seen_ids = set()

    try:
        resp = requests.get(
            ARBEITNOW_API,
            headers=HEADERS,
            params={"search": "machine learning intern"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
        for hit in data.get("data", []):
            job_id = str(hit.get("slug", ""))
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            company = hit.get("company_name", "")
            title = hit.get("title", "")
            location = hit.get("location", "Remote")
            description = hit.get("description", "")
            url = hit.get("url", "")

            job = normalize(
                company=company,
                title=title,
                location=location,
                description=description,
                url=url,
                source="lever",
            )
            if job:
                jobs.append(job)

    except Exception as e:
        print(f"[Arbeitnow] Failed: {e}")

    return jobs


def scrape_lever() -> list[dict]:
    """
    Search for ML intern jobs across all companies using
    Remotive and Arbeitnow aggregator APIs.
    """
    remotive_jobs = _scrape_remotive()
    arbeitnow_jobs = _scrape_arbeitnow()

    jobs = remotive_jobs + arbeitnow_jobs
    print(f"[Lever/Aggregators] Found {len(jobs)} relevant jobs "
          f"(Remotive: {len(remotive_jobs)}, Arbeitnow: {len(arbeitnow_jobs)})")
    return jobs


if __name__ == "__main__":
    results = scrape_lever()
    for j in results[:10]:
        print(f"  {j['company']} | {j['title']} | {j['location']}")
