import html
import requests
import time


def format_job(job) -> str:
    warnings = ""
    if job.warnings:
        warnings = "\n⚠️ " + " | ".join(job.warnings)
    posted = f"\n📅 {job.posted}" if job.posted else ""
    return (
        f"🟢 <b>{html.escape(job.company)}</b> — <b>{html.escape(job.title)}</b>\n"
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
