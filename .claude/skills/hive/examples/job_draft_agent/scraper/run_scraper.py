"""
debug_scrapers.py — tests the actual new scraper implementations
"""

import re
import sys
import json
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,*/*",
    "Accept-Language": "en-US,en;q=0.5",
}


def debug_yc():
    print("\n" + "=" * 60)
    print("YC DEBUG")
    print("=" * 60)
    url = "https://www.workatastartup.com/jobs.json"
    resp = requests.get(url, headers=HEADERS, params={"q": "machine learning intern"}, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('content-type', '')}")
    print(f"First 300 chars: {resp.text[:300]}")
    if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
        data = resp.json()
        print(f"Type: {type(data)}, Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")


def debug_jobicy():
    print("\n" + "=" * 60)
    print("JOBICY DEBUG (replaces Greenhouse)")
    print("=" * 60)
    url = "https://jobicy.com/api/v2/remote-jobs"
    resp = requests.get(url, headers=HEADERS, params={"search": "machine learning intern", "count": 5}, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        jobs = data.get("jobs", [])
        print(f"Jobs returned: {len(jobs)}")
        if jobs:
            print(f"Keys: {list(jobs[0].keys())}")
            for j in jobs[:3]:
                print(f"  {j.get('companyName','?')} | {j.get('jobTitle','?')} | {j.get('jobGeo','?')}")


def debug_muse():
    print("\n" + "=" * 60)
    print("THE MUSE DEBUG")
    print("=" * 60)
    url = "https://www.themuse.com/api/public/jobs"
    resp = requests.get(url, headers=HEADERS, params={"query": "machine learning intern", "level": "Internship", "page": 0}, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        results = data.get("results", [])
        print(f"Results: {len(results)}")
        if results:
            print(f"Keys: {list(results[0].keys())}")
            for j in results[:3]:
                company = (j.get("company") or {}).get("name", "?")
                locs = j.get("locations", [{}])
                loc = locs[0].get("name", "?") if locs else "?"
                print(f"  {company} | {j.get('name','?')} | {loc}")


def debug_remotive():
    print("\n" + "=" * 60)
    print("REMOTIVE DEBUG (replaces Lever)")
    print("=" * 60)
    url = "https://remotive.com/api/remote-jobs"
    resp = requests.get(url, headers=HEADERS, params={"search": "machine learning intern", "limit": 5}, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        jobs = data.get("jobs", [])
        print(f"Jobs returned: {len(jobs)}")
        if jobs:
            print(f"Keys: {list(jobs[0].keys())}")
            for j in jobs[:3]:
                print(f"  {j.get('company_name','?')} | {j.get('title','?')} | {j.get('candidate_required_location','?')}")


def debug_linkedin():
    print("\n" + "=" * 60)
    print("LINKEDIN DEBUG")
    print("=" * 60)
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": "machine learning intern",
        "location": "Canada",
        "geoId": "101174742",
        "f_TPR": "r604800",
        "f_E": "1",
        "start": 0,
        "count": 5,
    }
    resp = requests.get(url, headers={**HEADERS, "Accept": "text/html,*/*"}, params=params, timeout=15)
    print(f"Status: {resp.status_code}, Length: {len(resp.text)}")

    html = resp.text

    # Test all extraction patterns
    ids_urn = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', html)
    ids_href = re.findall(r'/jobs/view/(\d+)', html)
    titles_sr = re.findall(r'class="sr-only">\s*\n?\s*(.*?)\s*\n?\s*<', html)
    titles_card = re.findall(r'base-search-card__title[^>]*>\s*(.*?)\s*</', html)
    companies = re.findall(r'base-search-card__subtitle[^>]*>.*?<a[^>]*>\s*(.*?)\s*</', html, re.DOTALL)
    locations = re.findall(r'job-search-card__location[^>]*>\s*(.*?)\s*</', html)

    print(f"Job IDs (data-entity-urn): {ids_urn[:5]}")
    print(f"Job IDs (/jobs/view/):     {ids_href[:5]}")
    print(f"Titles (sr-only):          {titles_sr[:3]}")
    print(f"Titles (card title):       {titles_card[:3]}")
    print(f"Companies:                 {companies[:3]}")
    print(f"Locations:                 {locations[:3]}")

    if ids_urn:
        print(f"\n✓ LinkedIn parsing works — found {len(ids_urn)} job IDs")
    else:
        print("\n✗ No job IDs found — HTML structure may have changed")
        print(f"First 500 chars:\n{html[:500]}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=["yc", "jobicy", "muse", "remotive", "linkedin", "all"],
        default="all",
    )
    args = parser.parse_args()

    if args.source in ("yc", "all"):
        debug_yc()
    if args.source in ("jobicy", "all"):
        debug_jobicy()
    if args.source in ("muse", "all"):
        debug_muse()
    if args.source in ("remotive", "all"):
        debug_remotive()
    if args.source in ("linkedin", "all"):
        debug_linkedin()
