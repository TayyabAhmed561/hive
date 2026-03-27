import json
import hashlib
from pathlib import Path


CACHE_PATH = Path(__file__).resolve().parent.parent / "out" / "seen_jobs.json"


def _load_cache() -> set[str]:
    if CACHE_PATH.exists():
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return set(data)
    return set()


def _save_cache(seen: set[str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")


def job_hash(job: dict) -> str:
    """Stable hash based on company + title + location."""
    key = f"{job['company'].lower()}|{job['title'].lower()}|{job['location'].lower()}"
    return hashlib.md5(key.encode()).hexdigest()


def is_seen(job: dict) -> bool:
    seen = _load_cache()
    return job_hash(job) in seen


def mark_seen(job: dict) -> None:
    seen = _load_cache()
    seen.add(job_hash(job))
    _save_cache(seen)


def filter_new(jobs: list[dict]) -> list[dict]:
    """Return only jobs not in the seen cache, and mark them all as seen."""
    seen = _load_cache()
    new_jobs = []
    for job in jobs:
        h = job_hash(job)
        if h not in seen:
            new_jobs.append(job)
            seen.add(h)
    _save_cache(seen)
    return new_jobs
