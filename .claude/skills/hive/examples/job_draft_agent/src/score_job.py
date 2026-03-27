def score_job(job: dict, profile: dict) -> dict:
    job_keywords = set(job.get("keywords", []))
    profile_skills = set(profile.get("skills", []))
    profile_interests = set(profile.get("interests", []))
    preferred_locations = set(profile.get("locations", []))
    penalties = profile.get("penalties", {})

    skill_matches = sorted(job_keywords & profile_skills)
    interest_matches = sorted(job_keywords & profile_interests)

    score = 35
    score += min(len(skill_matches) * 5, 35)
    score += min(len(interest_matches) * 3, 12)

    raw_text = job["raw_text"].lower()
    location_text = job.get("location", "").lower()

    location_match = any(loc in location_text for loc in preferred_locations)
    if location_match:
        score += 8

    if "4 months" in raw_text or "4-6 months" in raw_text or "6 months" in raw_text:
        score += 5

    penalties_applied = []

    if "phd" in raw_text:
        penalty = penalties.get("phd_required", 12)
        score -= penalty
        penalties_applied.append(f"PhD requirement (-{penalty})")

    if "publication" in raw_text or "publications" in raw_text:
        penalty = penalties.get("publications_required", 8)
        score -= penalty
        penalties_applied.append(f"Publications preferred/required (-{penalty})")

    if "12 months" in raw_text:
        penalty = penalties.get("twelve_month_term", 15)
        score -= penalty
        penalties_applied.append(f"12 month term (-{penalty})")

    score = max(0, min(100, score))

    job["score"] = score
    job["skill_matches"] = skill_matches
    job["interest_matches"] = interest_matches
    job["location_match"] = location_match
    job["penalties_applied"] = penalties_applied
    return job
