from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    url: str
    posted: str = ""
    category: str = ""
    source: str = ""
    description: str = ""
    score: int = 0
    fit: str = ""
    warnings: list[str] = field(default_factory=list)
    gpa_cutoff: Optional[float] = None
    semesters_remaining: Optional[int] = None
    min_years_experience: Optional[int] = None
