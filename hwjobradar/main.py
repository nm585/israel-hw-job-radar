import argparse
import logging

from .config import load_config, telegram_credentials
from .fetchers import fetch_source, enrich_job
from .notify import notify_jobs, notify_text
from .scoring import score_job, is_candidate, is_student_or_part_time
from .storage import Storage

log = logging.getLogger("hwjobradar")


def run(config_path=None, dry_run=False, source_filter=None, no_seed=False, include_seen=False):
    cfg = load_config(config_path)
    storage = Storage(cfg["db_path"])
    token, chat_id = telegram_credentials()
    min_score = int(cfg.get("filters", {}).get("min_score", 48))
    source_fail_threshold = int(cfg.get("source_fail_alert_after", 2))

    first_run = storage.conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0] == 0
    candidates = []
    new_to_mark = []

    sources = [s for s in cfg.get("sources", []) if s.get("enabled", True)]
    if source_filter:
        sf = source_filter.lower()
        sources = [s for s in sources if sf in s.get("name", s.get("type", "")).lower()]

    for src in sources:
        name = src.get("name", src["type"])
        log.info("Checking %s", name)
        try:
            jobs = fetch_source(src)
            recovered = storage.record_success(name)
            if recovered and not dry_run:
                notify_text(token, chat_id, f"✅ Source recovered: {name}")
        except Exception as e:
            log.exception("Source failed: %s", name)
            if not dry_run and storage.record_failure(name, source_fail_threshold):
                notify_text(token, chat_id, f"⚠️ Job source failed twice: {name}. Check the adapter/config.")
            continue

        priority = int(src.get("priority", 0))
        for job in jobs:
            # Early title score avoids fetching every senior/nontechnical detail page.
            score_job(job, priority)
            if job.score < max(15, min_score - 30) and not is_student_or_part_time(job.title):
                continue
            if not include_seen and storage.seen(job.id):
                continue
            job, open_now = enrich_job(job)
            if not open_now:
                continue
            score_job(job, priority)
            if is_candidate(job, min_score):
                candidates.append(job)
            new_to_mark.append(job)

    # Default first run seeds current jobs silently, preventing an alert storm.
    if first_run and not no_seed and not include_seen and not dry_run:
        for job in new_to_mark:
            storage.mark_seen(job)
        log.info("Seeded %d current candidate-ish jobs; no notifications on first run.", len(new_to_mark))
        return candidates

    if dry_run:
        for job in sorted(candidates, key=lambda j: j.score, reverse=True):
            print(f"{job.score:3} {job.fit:6} | {job.company:22} | {job.title} | {job.location} | {job.url}")
            if job.warnings:
                print("    WARN:", "; ".join(job.warnings))
        return candidates

    log.info("Scan summary: %d matching jobs; include_existing=%s; Telegram configured=%s", len(candidates), include_seen, bool(token and chat_id))
    if candidates:
        notify_jobs(token, chat_id, candidates)
        log.info("Notification stage completed for %d matching jobs", len(candidates))

    # Mark only after notification stage. If Telegram raises, the run fails and jobs retry next run.
    for job in new_to_mark:
        storage.mark_seen(job)
    return candidates


def cli():
    p = argparse.ArgumentParser(description="Israel hardware/chip/quantum student job radar")
    p.add_argument("--config", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--source", default=None)
    p.add_argument("--no-seed", action="store_true", help="Alert/print existing matches on an empty database")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--include-seen", action="store_true", help="Send all current matches, including previously seen jobs (manual catch-up)")
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s")
    run(args.config, args.dry_run, args.source, args.no_seed, args.include_seen)
