"""
debug_scrapers.py

Run this to inspect raw responses from each source
so we can see exactly what's coming back and fix parsing.
"""

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

    url = "https://www.workatastartup.com/jobs/search.json"
    params = {"query": "machine learning intern", "remote": "true"}

    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('content-type', '')}")
    print(f"Response length: {len(resp.text)}")
    print(f"First 500 chars:\n{resp.text[:500]}")

    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f"\nJSON type: {type(data)}")
            if isinstance(data, list):
                print(f"List length: {len(data)}")
                if data:
                    print(f"First item keys: {list(data[0].keys())}")
                    print(f"First item:\n{json.dumps(data[0], indent=2)[:500]}")
            elif isinstance(data, dict):
                print(f"Dict keys: {list(data.keys())}")
                for k, v in data.items():
                    if isinstance(v, list) and v:
                        print(f"  {k}: list of {len(v)}, first item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
                    else:
                        print(f"  {k}: {str(v)[:100]}")
        except Exception as e:
            print(f"Not JSON: {e}")


def debug_greenhouse():
    print("\n" + "=" * 60)
    print("GREENHOUSE DEBUG")
    print("=" * 60)

    # Test a few tokens to see which ones work
    test_tokens = ["cohere", "cohere-ai", "anthropic", "huggingface", "shopify"]

    for token in test_tokens:
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            print(f"\nToken '{token}': status={resp.status_code}", end="")
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("jobs", [])
                company_name = data.get("name", token)
                print(f" | company='{company_name}' | {len(jobs)} jobs")
                if jobs:
                    print(f"  Sample titles: {[j['title'] for j in jobs[:3]]}")
            else:
                print(f" | {resp.text[:100]}")
        except Exception as e:
            print(f"\nToken '{token}': ERROR {e}")


def debug_lever():
    print("\n" + "=" * 60)
    print("LEVER DEBUG")
    print("=" * 60)

    test_tokens = ["cohere", "scale-ai", "uber", "stripe", "airbnb"]

    for token in test_tokens:
        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            print(f"\nToken '{token}': status={resp.status_code}", end="")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f" | {len(data)} postings")
                    if data:
                        print(f"  Sample titles: {[j.get('text','') for j in data[:3]]}")
                else:
                    print(f" | unexpected type: {type(data)}")
            else:
                print(f" | {resp.text[:100]}")
        except Exception as e:
            print(f"\nToken '{token}': ERROR {e}")


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

    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('content-type', '')}")
    print(f"Response length: {len(resp.text)}")
    print(f"\nFirst 1000 chars of response:\n{resp.text[:1000]}")

    import re
    job_ids = re.findall(r'data-job-id="(\d+)"', resp.text)
    job_ids_2 = re.findall(r'"jobPostingId":"(\d+)"', resp.text)
    job_ids_3 = re.findall(r'/jobs/view/(\d+)', resp.text)
    print(f"\nJob IDs found (data-job-id): {job_ids[:5]}")
    print(f"Job IDs found (jobPostingId): {job_ids_2[:5]}")
    print(f"Job IDs found (/jobs/view/): {job_ids_3[:5]}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["yc", "greenhouse", "lever", "linkedin", "all"],
                        default="all")
    args = parser.parse_args()

    if args.source in ("yc", "all"):
        debug_yc()
    if args.source in ("greenhouse", "all"):
        debug_greenhouse()
    if args.source in ("lever", "all"):
        debug_lever()
    if args.source in ("linkedin", "all"):
        debug_linkedin()
