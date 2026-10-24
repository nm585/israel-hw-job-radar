from hwjobradar.models import Job
from hwjobradar.scoring import score_job, is_candidate


def job(title, description=""):
    return Job(id="x", title=title, company="Test", location="Israel", url="https://example.com", description=description)


def test_student_rtl_is_high_fit():
    j = job("RTL Design Student", "SystemVerilog FPGA computer architecture Python")
    score_job(j, 10)
    assert j.score >= 75
    assert j.fit == "HIGH"


def test_senior_role_is_penalized():
    j = job("Senior RTL Design Engineer", "SystemVerilog UVM ASIC SoC")
    score_job(j, 10)
    assert j.score < 75


def test_gpa_and_semester_constraints_are_flagged():
    j = job("Digital Design Student", "Minimum average 90. At least 4 semesters remaining. Verilog RTL.")
    score_job(j, 10)
    assert j.gpa_cutoff == 90
    assert j.semesters_remaining == 4
    assert any("GPA" in w for w in j.warnings)
    assert any("semesters" in w for w in j.warnings)


def test_experience_requirement_penalized():
    j = job("Verification Engineer", "Requires 5+ years of experience with SystemVerilog UVM design verification")
    score_job(j, 10)
    assert j.min_years_experience == 5
    assert j.score < 50
    assert any("years" in w for w in j.warnings)


def test_firmware_student_can_pass():
    j = job("Firmware Student", "Embedded C C++ Linux low-level hardware software integration. No prior experience required.")
    score_job(j, 8)
    assert is_candidate(j, 48)


def test_no_experience_filter_is_mandatory_even_for_high_scores():
    from hwjobradar.scoring import allows_no_prior_experience
    for description in ["4 years of experience", "Requires four years of experience", "1+ years in ASIC design", "Prior work experience required", "Junior welcome", "No experience required. Minimum 4 years of experience", "נדרש 4 שנות ניסיון"]:
        j = job("Junior RTL Engineer", description)
        j.score = 100
        assert not is_candidate(j), description
    for description in ["No prior experience required", "No professional experience is required", "Prior experience is not required", "0-2 years of experience", "ללא ניסיון קודם"]:
        assert allows_no_prior_experience(job("RTL Engineer", description)), description
    assert not allows_no_prior_experience(job("Student Intern", "RTL and FPGA skills"))
