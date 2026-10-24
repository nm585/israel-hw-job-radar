import pytest
from hwjobradar.models import Job
from hwjobradar.notify import format_job, job_labels


@pytest.mark.parametrize("title,description,track,hours", [
    ("Junior RTL Engineer", "Full-time", "🔵 ג׳וניור — משרה מלאה", "🔵 היקף: משרה מלאה"),
    ("Junior RTL Engineer", "Part-time", "🟢 ג׳וניור — משרה חלקית", "🟣 היקף: משרה חלקית"),
    ("Entry-level RTL Engineer", "Full-time", "🔵 משרת כניסה / בוגרים — משרה מלאה", "🔵 היקף: משרה מלאה"),
    ("RTL Student", "Full-time position", "🟢 סטודנט / התמחות", "🔵 היקף: משרה מלאה"),
    ("DV Intern", "Part-time", "🟢 סטודנט / התמחות", "🟣 היקף: משרה חלקית"),
    ("Junior Firmware Engineer", "", "⚪ ג׳וניור — היקף לא ברור", "⚪ היקף: לא צוין"),
    ("Entry-level Engineer", "", "⚪ משרת כניסה / בוגרים — היקף לא ברור", "⚪ היקף: לא צוין"),
    ("Student Intern", "", "🟢 סטודנט / התמחות", "⚪ היקף: לא צוין"),
    ("RTL Engineer", "Mentor junior engineers and students.", "❔ סוג תפקיד: לא צוין", "⚪ היקף: לא צוין"),
    ("סטודנטית חומרה", "משרה חלקית", "🟢 סטודנט / התמחות", "🟣 היקף: משרה חלקית"),
    ("Engineer", "Full-time or part-time", "❔ סוג תפקיד: לא צוין", "↔️ היקף: מלאה / חלקית — יש לבדוק במודעה"),
    ("Engineer", "Benefits for full-time employees.", "❔ סוג תפקיד: לא צוין", "⚪ היקף: לא צוין"),
    ("Engineer", "Not full-time. Part-time position.", "❔ סוג תפקיד: לא צוין", "🟣 היקף: משרה חלקית"),
])
def test_independent_labels(title, description, track, hours):
    job = Job("1", title, "Company", "Israel", "https://example.com", description=description)
    assert job_labels(job) == (track, hours)
    message = format_job(job)
    assert track in message and hours in message


@pytest.mark.parametrize("location,badge", [
    ("Tel Aviv-Yafo, Israel", "🟢"), ("Herzliya", "🟢"), ("Ra'anana", "🟢"),
    ("Petah-Tikva", "🟢"), ("Hod Hasharon", "🟢"), ("Kfar Saba", "🟢"),
    ("פתח תקווה", "🟢"), ("חיפה", "🟠"), ("Jerusalem", "🟠"),
    ("Rehovot", "🟠"), ("Be'er Sheva", "🟠"), ("Yokneam", "⚪"),
    ("Israel", "⚪"), ("Tel Aviv / Haifa", "⚪"),
])
def test_location_badges(location, badge):
    from hwjobradar.notify import location_badge
    assert location_badge(location).startswith(badge)
