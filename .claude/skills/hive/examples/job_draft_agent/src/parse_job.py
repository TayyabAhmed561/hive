import re

SKILL_KEYWORDS = [
    "python", "pytorch", "tensorflow", "jax", "sql", "c++", "c",
    "transformers", "nlp", "llms", "evaluation", "multimodal",
    "distributed training", "deep learning", "machine learning",
    "data pipelines", "experimentation", "cross-validation"
]

KNOWN_COMPANIES = {
    "cohere": "Cohere",
    "pinterest": "Pinterest",
    "fairwai": "FairwAI",
    "openai": "OpenAI",
    "google": "Google",
}


def parse_jsonish_field(raw_text: str, field_name: str) -> str | None:
    pattern = rf'"{re.escape(field_name)}"\s*:\s*"([^"]+)"'
    match = re.search(pattern, raw_text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def clean_line(line: str) -> str:
    line = line.strip().strip(",")
    line = line.strip('"')
    return line.strip()


def is_junk_line(line: str) -> bool:
    low = line.lower().strip()

    if not low:
        return True

    junk_exact = {
        "{", "}", "[", "]", "apply", "save", "show more options",
        "your ai-powered job assessment", "tailor my resume",
        "create cover letter", "help me stand out",
    }

    if low in junk_exact:
        return True

    if low.startswith('"title"'):
        return True
    if low.startswith('"company"'):
        return True
    if low.startswith('"location"'):
        return True
    if low.startswith('"requirements"'):
        return True

    if low.endswith(":"):
        return True

    return False


def looks_like_title(line: str) -> bool:
    low = line.lower()

    bad_substrings = [
        "apply", "save", "hybrid", "full-time", "reposted",
        "responses managed", "show more", "your ai-powered",
        "requirements", "preferred qualifications",
    ]

    if any(x in low for x in bad_substrings):
        return False

    if len(line) < 5:
        return False

    return True


def parse_job(raw_text: str) -> dict:
    title = parse_jsonish_field(raw_text, "title") or "Unknown Role"
    company = parse_jsonish_field(raw_text, "company") or "Unknown Company"
    location = parse_jsonish_field(raw_text, "location") or "Unknown Location"

    lower_text = raw_text.lower()

    if company == "Unknown Company":
        for key, pretty in KNOWN_COMPANIES.items():
            if key in lower_text:
                company = pretty
                break

    raw_lines = [clean_line(line) for line in raw_text.splitlines()]
    lines = [line for line in raw_lines if not is_junk_line(line)]

    if title == "Unknown Role":
        for line in lines[:20]:
            if looks_like_title(line):
                title = line
                break

    if location == "Unknown Location":
        for line in lines[:25]:
            low = line.lower()
            if any(loc in low for loc in ["toronto", "remote", "waterloo", "hybrid", "ontario"]):
                location = line
                break

    found_keywords = [kw for kw in SKILL_KEYWORDS if kw in lower_text]

    return {
        "title": title,
        "company": company,
        "location": location,
        "keywords": found_keywords,
        "raw_text": raw_text,
    }
