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
    for description in ["4 years of experience", "Requires four years of experience", "1+ years in ASIC design", "Prior work experience required", "No experience required. Minimum 4 years of experience", "נדרש 4 שנות ניסיון"]:
        j = job("Junior RTL Engineer", description)
        j.score = 100
        assert not is_candidate(j), description
    for description in ["No prior experience required", "No professional experience is required", "Prior experience is not required", "0-2 years of experience", "ללא ניסיון קודם"]:
        assert allows_no_prior_experience(job("Junior RTL Engineer", description)), description
    assert allows_no_prior_experience(job("Student Intern", "RTL and FPGA skills"))


def test_non_entry_title_is_blocked_even_with_no_experience_text():
    from hwjobradar.scoring import allows_no_prior_experience
    assert not allows_no_prior_experience(job("RTL Engineer", "No prior experience required"))
    assert not allows_no_prior_experience(job("Junior RTL Engineer", "No experience required. 4 years Verilog."))


def test_hardware_project_skills_are_recognized():
    from hwjobradar.scoring import _sum_matches, SKILL_BONUS, DOMAIN_WEIGHTS
    assert _sum_matches("C++", SKILL_BONUS) == 4
    assert _sum_matches("VHDL RISC-V ModelSim SignalTap Quartus CDC", SKILL_BONUS) == 29
    assert _sum_matches("High-level synthesis", DOMAIN_WEIGHTS) >= 20
    assert _sum_matches("HLS", DOMAIN_WEIGHTS) >= 20


def test_entry_examples_without_magic_no_experience_sentence():
    from hwjobradar.scoring import allows_no_prior_experience
    cases = [
        ("Electrical Engineering Graduate", "DFT training program. B.Sc. Electrical Engineering. Graduates or students in their 8th semester. Preferred: chip design experience."),
        ("CAD/Emulation Graduate Engineer", "Entry-level role. Python required. Academic level VLSI / ASIC / verification is sufficient."),
        ("Design Verification- Intern", "Electrical Engineering student. Verilog and digital design skills."),
    ]
    for title, description in cases:
        j = job(title, description)
        score_job(j, 12)
        assert is_candidate(j), title
        for requirement in ["Minimum 4 years of experience", "Previous professional experience required", "Requires two years of experience"]:
            assert not allows_no_prior_experience(job(title, description + ". " + requirement))
    assert not allows_no_prior_experience(job("Design Verification Intern", ""))
