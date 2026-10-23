import html
import re
import requests
import time


def job_labels(job) -> tuple[str, str]:
    """Keep career track and hours independent; never infer hours from student status."""
    title = job.title or ""
    tracks = []
    for pattern, label in (
        (r"\bstudents?\b|סטודנט(?:ית|ים|יות)?", "🎓 סטודנט"),
        (r"\bintern(?:ship)?\b|התמחות|מתמחה", "🧪 התמחות"),
        (r"\bjunior\b|\bjr\.?\b|ג[׳']?וניור", "🌱 ג׳וניור"),
        (r"\bentry[ -]?level\b|\b(?:new|recent) grad(?:uate)?\b|\bgraduate(?: engineer| program| role)?\b|משרת כניסה", "🚪 משרת כניסה / בוגרים"),
    ):
        if re.search(pattern, title, re.I):
            tracks.append(label)
    track = " · ".join(tracks) or "❔ סוג תפקיד: לא צוין"
    # Ignore navigation/benefit text and explicit negations rather than guessing.
    evidence = f"{title}. {job.description or ''}"
    full = part = False
    for sentence in re.split(r"[.!?;\n]", evidence):
        if re.search(r"benefits?|equal opportunity|we hire|all employees|הטבות", sentence, re.I):
            continue
        sentence = re.sub(r"\b(?:not|no)\s+(?:a\s+)?(?:full|part)[ -]?time\b|לא\s+משרה\s+(?:מלאה|חלקית)", "", sentence, flags=re.I)
        full |= bool(re.search(r"\bfull[ -]?time\b|משרה מלאה", sentence, re.I))
        part |= bool(re.search(r"\bpart[ -]?time\b|משרה חלקית", sentence, re.I))
    if full and part:
        hours = "↔️ היקף: מלאה / חלקית — יש לבדוק במודעה"
    elif full:
        hours = "🔵 היקף: משרה מלאה"
    elif part:
        hours = "🟣 היקף: משרה חלקית"
    else:
        hours = "⚪ היקף: לא צוין"
    if any("סטודנט" in label or "התמחות" in label for label in tracks):
        track = "🟢 סטודנט / התמחות"
    elif any("ג׳וניור" in label or "משרת כניסה" in label for label in tracks):
        names = " / ".join("ג׳וניור" if "ג׳וניור" in label else "משרת כניסה / בוגרים" for label in tracks)
        if part and not full:
            track = "🟢 " + names + " — משרה חלקית"
        elif full and not part:
            track = "🔵 " + names + " — משרה מלאה"
        else:
            track = "⚪ " + names + " — היקף לא ברור"
    return track, hours


def format_job(job) -> str:
    track, hours = job_labels(job)
    warnings = ""
    if job.warnings:
        warnings = "\n⚠️ " + " | ".join(job.warnings)
    posted = f"\n📅 {job.posted}" if job.posted else ""
    return (
        f"<b>{html.escape(job.company)}</b> — <b>{html.escape(job.title)}</b>\n"
        f"{track}\n{hours}\n"
        f"📍 {html.escape(job.location or 'Israel')}"
        f"{posted}\n"
        f"🎯 Fit: <b>{job.fit}</b> ({job.score}/100)"
        f"{warnings}\n"
        f"🔗 <a href=\"{html.escape(job.url, quote=True)}\">Official posting</a>"
    )


def send_telegram(token: str, chat_id: str, text: str) -> None:
    if not token or not chat_id:
        print(text.replace("<b>", "").replace("</b>", ""))
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=20,
    )
    r.raise_for_status()


def notify_jobs(token: str, chat_id: str, jobs: list) -> None:
    for job in sorted(jobs, key=lambda j: j.score, reverse=True):
        send_telegram(token, chat_id, format_job(job))
        if token and chat_id:
            time.sleep(1.1)


def notify_text(token: str, chat_id: str, text: str) -> None:
    send_telegram(token, chat_id, html.escape(text))
