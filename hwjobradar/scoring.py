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
    r"\bhigh[ -]level synthesis\b|\bhls\b": 20,
    r"\bfirmware\b": 16,
    r"\bembedded\b": 16,
    r"\bhardware validation\b": 14,
    r"\bhw validation\b": 14,
    r"\bhardware engineering\b": 24,
    r"\bsystem integration\b": 18,
    r"\bsignal integrity\b": 22,
    r"\bpower integrity\b": 20,
    r"\bvlsi\b": 22,
    r"\boptical\b|\boptics\b|\bphotonic": 18,
    r"\blayout\b": 18,
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
    r"\bresearch scientist\b",
]

SKILL_BONUS = {
    r"\bvhdl\b": 8,
    r"\bverilog\b": 5,
    r"\bsystemverilog\b": 6,
    r"\buvm\b": 6,
    r"(?<!\w)c\+\+(?!\w)": 4,
    r"\bpython\b": 4,
    r"\blinux\b": 3,
    r"\brisc.?v\b": 7,
    r"\bquartus\b": 4,
    r"\bmodelsim\b": 4,
    r"\bsignaltap\b": 3,
    r"\bclock[ -]domain crossing\b|\bcdc\b": 3,
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


def is_student_or_part_time(text: str) -> bool:
    return bool(re.search(r"\bstudents?\b|\bintern(?:ship)?\b|\bworking student\b|\bpart[ -]?time\b|סטודנט|התמחות|מתמחה|משרה\s+חלקית", text, re.I))


def score_job(job: Job, company_priority: int = 0) -> Job:
    title = job.title or ""
    full = f"{title}\n{job.category}\n{job.description}"

    score = 0
    score += min(_sum_matches(full, DOMAIN_WEIGHTS), 55)
    score += min(_sum_matches(full, SKILL_BONUS), 15)
    score += company_priority

    if is_student_or_part_time(full) or any(re.search(p, title, re.I) for p in STUDENT_PATTERNS):
        score += 24
    elif re.search(r"\bengineer\b", title, re.I):
        score += 5

    if any(re.search(p, title, re.I) for p in SENIOR_PATTERNS):
        score -= 55

    # Software-only roles are noise unless the description has meaningful HW/low-level signals.
    software_tasks = bool(re.search(r"\bfull[ -]?stack applications\b|\breact\b|\bweb applications\b", job.description, re.I))
    if any(re.search(p, title, re.I) for p in NOISE_PATTERNS) or software_tasks:
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


def allows_no_prior_experience(job: Job) -> bool:
    """Entry-track titles qualify unless the posting requires prior experience."""
    text = f"{job.title}\n{job.description}".lower()
    for word, number in (("one", "1"), ("two", "2"), ("three", "3"), ("four", "4"), ("five", "5"), ("six", "6"), ("seven", "7"), ("eight", "8"), ("nine", "9"), ("ten", "10")):
        text = re.sub(r"\b" + word + r"\b", number, text)
    if any(re.search(p, job.title, re.I) for p in SENIOR_PATTERNS):
        return False
    entry_title = r"\bstudents?\b|\bintern(?:ship)?\b|\bjunior\b|\bjr\b|\bentry[ -]?level\b|\b(?:new|recent) grad(?:uate)?\b|\bgraduate\b|סטודנט|התמחות|מתמחה|ג[׳']?וניור|משרת כניסה"
    # Remove zero-minimum ranges before checking positive year/month requirements.
    clean = re.sub(r"\b0\s*[-–]\s*\d+\s*(?:years?|months?)\s*(?:of\s*)?(?:professional\s*|prior\s*|relevant\s*)?experience", "", text)
    # Education and placement duration are not prior work requirements.
    duration = r"\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?)?\s*(?:years?|months?)"
    education = (
        duration + r"\s*\)?\s*(?:(?:remaining|left)\s+)?(?:before|until|till|to)\s+graduation\b",
        duration + r"\s+(?:remaining|left)\s+(?:in|of|to complete)\s+(?:the |a |your )?(?:degree|studies|program)\b",
        duration + r"\s+of\s+(?:their |your |the )?studies\s+(?:still\s+)?(?:remaining|left)\b",
        duration + r"\s+(?:internship|training|program|placement)\b",
    )
    for pattern in education:
        clean = re.sub(pattern, "", clean)
    clean = re.sub(r"\b(?:b\.?sc\.?|m\.?sc\.?|bachelor|master)[^.;]{0,150}?\bstudent[^.;]{0,120}?\bwith\s+\d+(?:\.\d+)?\+?\s+years?\s+left\b", "", clean)
    # Experience explicitly described as an advantage is optional. A required
    # minimum elsewhere in the same posting is still checked below.
    optional = r"\b\d+(?:\.\d+)?\s*(?:[-–]\s*\d+)?\s*(?:years?|months?)\s+(?:(?:of|relevant|professional|prior|work|industry)\s+)*(?:experience\s*)?(?:is\s+)?(?:an?\s+)?(?:advantage|plus|preferred|nice.to.have)\b"
    clean = re.sub(optional, "", clean)
    if re.search(r"\b[1-9]\d*\s*(?:\+|[-–]\s*\d+)?\s*(?:years?|months?)\b", clean):
        return False
    if re.search(r"\b[1-9]\d*\s*(?:\+|[-–]\s*\d+)?\s*(?:years?|months?)(?:\s+of)?\s+(?:(?:relevant|professional|prior|industry|hands-on|work)\s+)?(?:experience|in\b|working\b|developing\b|designing\b)", clean):
        return False
    if re.search(r"experience\s*(?:of|:|minimum|at least)?\s*[1-9]\d*\s*\+?\s*(?:years?|months?)|[1-9]\d*\s*(?:שנות|שנים|חודשי)\s*ניסיון", clean):
        return False
    clean = re.sub(r"\bno\s+(?:(?:prior|previous|professional|work|industry)\s+)*experience\s+(?:is\s+)?(?:required|needed|necessary)\b", "", clean)
    if re.search(r"(?:must have|required|requires|minimum)\s+(?:prior|previous|professional|industry|commercial|work)\s+experience|(?:prior|previous|professional|industry|commercial|work)\s+experience\s+(?:is\s+)?required", clean):
        return False
    # An explicit entry-track title is evidence of eligibility; do not demand
    # an artificial "no experience required" sentence. Missing details still fail closed.
    return bool(job.description.strip())



def is_candidate(job: Job, min_score: int = 48) -> bool:
    non_engineering = r"\b(?:product|project|program) management\b|\bproduct manager\b|\bsales\b|\bmarketing\b|\bfinance\b|\bhuman resources\b|\brecruit(?:er|ing|ment)\b"
    if re.search(non_engineering, job.title, re.I):
        return False
    if not requested_work_type(job):
        return False
    if re.search(r"\bjunior\b|\bjr\.?\b|ג[׳']?וניור", job.title, re.I):
        return False
    entry = r"\bentry[ -]?level\b|\b(?:new|recent) grad(?:uate)?s?\b|\bgraduates?\b|משרת?\s+כניסה|משרות\s+כניסה|בוגר(?:ים|ות)?"
    if re.search(entry, job.title, re.I) and not is_student_or_part_time(job.title):
        return False
    return job.score >= min_score and allows_no_prior_experience(job)


def requested_work_type(job: Job) -> bool:
    """Require student/intern/part-time evidence, not just absence of seniority."""
    if is_student_or_part_time(job.title) or is_student_or_part_time(job.category):
        return True
    text = job.description or ""
    text = re.sub(r"\b(?:not|no)\s+(?:a\s+)?part[ -]?time\b|לא\s+משרה\s+חלקית", "", text, flags=re.I)
    return bool(re.search(
        r"\bpart[ -]?time\s+(?:position|role|job|internship)\b"
        r"|\b(?:time type|employment type|work schedule)\s*:?\s*part[ -]?time\b"
        r"|\bcurrently\s+(?:enrolled|pursuing)\b.{0,100}\b(?:degree|bachelor|master|bsc|msc)\b"
        r"|\b(?:student|internship)\s+(?:position|role)\b"
        r"|\bworking student\b"
        r"|משרת\s+סטודנט|משרה\s+חלקית", text, re.I))
