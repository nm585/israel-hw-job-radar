import re
from .models import Job

# Highest priority: chip design / verification / DFT
DOMAIN_WEIGHTS = {
    r"\brtl\b": 30,
    r"\blogic design\b": 30,
    r"\bdigital design\b": 30,
    r"\bchip design\b": 28,
    r"\bdesign verification\b": 30,
    r"\bverification\b": 22,
    r"\bformal verification\b": 30,
    r"\bdft\b": 30,
    r"\batpg\b": 30,
    r"\bscan\b": 20,
    r"\basic\b": 24,
    r"\bsoc\b": 24,
    r"\bfpga\b": 24,
    r"\bmicro.?arch": 24,
    r"\bcomputer architecture\b": 20,
    r"\bpost.?silicon\b": 20,
    r"\bsilicon validation\b": 20,
    r"\bemulation\b": 18,
    r"\bfirmware\b": 16,
    r"\bembedded\b": 16,
    r"\bhardware validation\b": 14,
    r"\bhardware.?software\b": 12,
}

STUDENT_PATTERNS = [
    r"\bstudent\b", r"\bintern\b", r"\binternship\b", r"\bworking student\b",
    r"\bpart.?time\b", r"\bgraduate\b", r"\bjunior\b", r"\bentry.?level\b",
]

SENIOR_PATTERNS = [
    r"\bsenior\b", r"\bstaff\b", r"\bprincipal\b", r"\bdirector\b",
    r"\bmanager\b", r"\bteam lead\b", r"\blead engineer\b", r"\bsr\.?\b",
]

NOISE_PATTERNS = [
    r"\bqa automation\b", r"\bsoftware qa\b", r"\bweb developer\b",
    r"\bfrontend\b", r"\bfront.?end\b", r"\bbackend\b", r"\bfull.?stack\b",
    r"\bdata scientist\b", r"\bproduct manager\b", r"\bsales\b",
]

SKILL_BONUS = {
    r"\bvhdl\b": 5,
    r"\bverilog\b": 5,
    r"\bsystemverilog\b": 6,
    r"\buvm\b": 6,
    r"\bc\+\+\b": 4,
    r"\bpython\b": 4,
    r"\blinux\b": 3,
    r"\brisc.?v\b": 5,
    r"\bquartus\b": 3,
}


def _sum_matches(text: str, mapping: dict[str, int]) -> int:
    return sum(weight for pat, weight in mapping.items() if re.search(pat, text, re.I))


def detect_constraints(job: Job) -> None:
    text = f"{job.title}\n{job.description}"

    # GPA / average. Conservative: only explicit 80-100 style thresholds.
    gpa_patterns = [
        r"(?:gpa|average|grade average|ממוצע)\D{0,15}(8\d|9\d|100)(?:\s*\+|\s*or above|\s*and above)?",
        r"(8\d|9\d|100)\s*\+\s*(?:gpa|average)?",
    ]
    for pat in gpa_patterns:
        m = re.search(pat, text, re.I)
        if m:
            job.gpa_cutoff = float(m.group(1))
            if job.gpa_cutoff > 84:
                job.warnings.append(f"GPA/average cutoff appears to be {job.gpa_cutoff:g}+")
            break

    sem_patterns = [
        r"at least\s+(\d+)\s+(?:full\s+)?semesters?\s+(?:remaining|left)",
        r"minimum\s+of\s+(\d+)\s+semesters?\s+(?:remaining|left)",
        r"(\d+)\s+semesters?\s+(?:remaining|left)",
        r"לפחות\s+(\d+)\s+סמסטרים",
    ]
    for pat in sem_patterns:
        m = re.search(pat, text, re.I)
        if m:
            job.semesters_remaining = int(m.group(1))
            if job.semesters_remaining >= 3:
                job.warnings.append(f"Requires about {job.semesters_remaining}+ semesters remaining")
            break

    exp_patterns = [
        r"(?:minimum|min\.?|at least|requires?|required|with)\s+(\d+)\+?\s+years?\s+(?:of\s+)?(?:relevant\s+)?experience",
        r"(\d+)\s*[-–]\s*\d+\s+years?\s+(?:of\s+)?experience",
        r"(\d+)\+\s+years?\s+(?:of\s+)?experience",
    ]
    years = []
    for pat in exp_patterns:
        for m in re.finditer(pat, text, re.I):
            try:
                years.append(int(m.group(1)))
            except (TypeError, ValueError):
                pass
    if years:
        job.min_years_experience = min(years)
        if job.min_years_experience >= 3:
            job.warnings.append(f"Asks for {job.min_years_experience}+ years of experience")


def score_job(job: Job, company_priority: int = 0) -> Job:
    title = job.title or ""
    full = f"{title}\n{job.category}\n{job.description}"

    score = 0
    score += min(_sum_matches(full, DOMAIN_WEIGHTS), 55)
    score += min(_sum_matches(full, SKILL_BONUS), 15)
    score += company_priority

    if any(re.search(p, title, re.I) for p in STUDENT_PATTERNS):
        score += 24
    elif re.search(r"\bengineer\b", title, re.I):
        score += 5

    if any(re.search(p, title, re.I) for p in SENIOR_PATTERNS):
        score -= 55

    # Software-only roles are noise unless the description has meaningful HW/low-level signals.
    if any(re.search(p, title, re.I) for p in NOISE_PATTERNS):
        hw_signal = _sum_matches(full, DOMAIN_WEIGHTS)
        if hw_signal < 18:
            score -= 35

    detect_constraints(job)
    if job.gpa_cutoff and job.gpa_cutoff > 84:
        score -= 18
    if job.semesters_remaining and job.semesters_remaining >= 4:
        score -= 22
    elif job.semesters_remaining == 3:
        score -= 10
    if job.min_years_experience and job.min_years_experience >= 5:
        score -= 45
    elif job.min_years_experience and job.min_years_experience >= 3:
        score -= 28
    elif job.min_years_experience == 2:
        score -= 8

    job.score = max(0, min(100, score))
    if job.score >= 75:
        job.fit = "HIGH"
    elif job.score >= 50:
        job.fit = "MEDIUM"
    else:
        job.fit = "LOW"
    return job


def is_candidate(job: Job, min_score: int = 48) -> bool:
    return job.score >= min_score
