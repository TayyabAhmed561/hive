from datetime import date


ML_KEYWORDS = {
    "machine learning", "machine learning engineer", "ml", "deep learning", "neural network", "nlp",
    "natural language processing", "computer vision", "research", "pytorch",
    "tensorflow", "reinforcement learning", "llm", "large language model",
    "multimodal", "transformer", "diffusion", "generative", "ai", "artificial intelligence",
    "data science", "model training", "inference", "evaluation", "fine-tuning",
    "foundation model", "embeddings", "rag", "retrieval", "experiment",
}

INTERN_KEYWORDS = {
    "intern", "internship", "co-op", "coop", "co op", "student", "new grad",
    "entry level", "junior", "summer 2026", "fall 2026", "winter 2026", "spring 2026",
}

LOCATION_KEYWORDS = {
    "canada", "remote", "toronto", "montreal", "vancouver", "waterloo",
    "ottawa", "calgary", "edmonton", "hybrid", "anywhere",
}

EXCLUDE_KEYWORDS = {
    "senior", "staff", "principal", "director", "manager", "lead", "vp", "head of",
    "10+ years", "8+ years", "7+ years",
}


def is_ml_relevant(title: str, description: str) -> bool:
    text = (title + " " + description).lower()
    return any(kw in text for kw in ML_KEYWORDS)


def is_intern_level(title: str, description: str) -> bool:
    text = (title + " " + description).lower()
    return any(kw in text for kw in INTERN_KEYWORDS)


def is_location_match(location: str, description: str) -> bool:
    text = (location + " " + description).lower()
    return any(kw in text for kw in LOCATION_KEYWORDS)


def is_excluded(title: str, description: str) -> bool:
    text = (title + " " + description).lower()
    return any(kw in text for kw in EXCLUDE_KEYWORDS)


def normalize(
    company: str,
    title: str,
    location: str,
    description: str,
    url: str,
    source: str,
) -> dict | None:
    """
    Normalize a raw job into a standard dict.
    Returns None if the job doesn't pass filters.
    """
    if not is_ml_relevant(title, description):
        return None
    if not is_intern_level(title, description):
        return None
    if not is_location_match(location, description):
        return None
    if is_excluded(title, description):
        return None

    return {
        "company": company.strip(),
        "title": title.strip(),
        "location": location.strip() or "Remote",
        "description": description.strip(),
        "url": url.strip(),
        "source": source,
        "scraped_at": date.today().isoformat(),
    }
