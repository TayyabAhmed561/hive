"""Configuration for Job Application Agent."""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class AgentMetadata:
    name: str
    version: str
    description: str
    author: str = "Tayyab Ahmed"
    tags: list = field(default_factory=list)


@dataclass
class AgentConfig:
    model: str = "openai/gpt-4o"
    max_tokens: int = 4096
    api_key: Optional[str] = None
    api_base: Optional[str] = None

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")


metadata = AgentMetadata(
    name="Job Application Agent",
    version="1.0.0",
    description=(
        "Paste a job description and get a tailored resume and cover letter "
        "compiled as PDFs — with a match score and summary of what changed."
    ),
    tags=["career", "resume", "jobs", "productivity"],
)

default_config = AgentConfig()
