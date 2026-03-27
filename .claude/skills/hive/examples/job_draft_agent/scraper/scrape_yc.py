import requests
from normalize import normalize

# workatastartup.com job search
YC_API_URL = "https://www.workatastartup.com/jobs.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.workatastartup.com/jobs",
}

SEARCH_TERMS = [
    "machine learning",
    "ml engineer",
    "research intern",
    "ai engineer",
    "deep learning",
    "nlp",
    "computer vision",
    "data science",
]


def scrape_yc() -> list[dict]:
    jobs = []
    seen_ids = set()

    for term in SEARCH_TERMS:
        try:
            resp = requests.get(
                YC_API_URL,
                headers=HEADERS,
                params={"q": term, "jobType": "intern", "remote": "yes"},
                timeout=15,
            )
            if resp.status_code != 200:
                resp = requests.get(
                    YC_API_URL,
                    headers=HEADERS,
                    params={"q": term},
                    timeout=15,
                )

            if resp.status_code != 200:
                continue

            content_type = resp.headers.get("content-type", "")
            if "json" not in content_type:
                continue

            data = resp.json()
            postings = data if isinstance(data, list) else data.get("jobs", data.get("results", []))

            for hit in postings:
                job_id = str(hit.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                company = (
                    hit.get("company_name")
                    or (hit.get("company") or {}).get("name", "")
                    or ""
                )
                title = hit.get("title", "") or hit.get("role", "")
                location = hit.get("location", "") or ("Remote" if hit.get("remote") else "")
                description = hit.get("body", "") or hit.get("description", "") or title
                url = hit.get("url", "") or f"https://www.workatastartup.com/jobs/{job_id}"

                job = normalize(
                    company=company,
                    title=title,
                    location=location,
                    description=description,
                    url=url,
                    source="yc",
                )
                if job:
                    jobs.append(job)

        except Exception as e:
            print(f"[YC] Failed for '{term}': {e}")

    print(f"[YC] Found {len(jobs)} relevant jobs")
    return jobs


if __name__ == "__main__":
    results = scrape_yc()
    for j in results[:10]:
        print(f"  {j['company']} | {j['title']} | {j['location']}")
