"""Explicitly requested catch-up; send only reviewed URLs through current filters."""
import argparse
import logging
from pathlib import Path
import yaml

from .config import load_config, telegram_credentials
from .fetchers import enrich_job
from .models import Job
from .notify import notify_jobs
from .scoring import score_job, is_candidate
from .storage import Storage

log = logging.getLogger("hwjobradar.catchup")


def run_catchup(manifest, dry_run=False):
    cfg = load_config()
    data = yaml.safe_load(Path(manifest).read_text(encoding="utf-8")) or {}
    entries = data.get("jobs") or []
    if not entries:
        raise ValueError("Catch-up list is empty; refusing a broader scan")
    sources = {s["name"]: s for s in cfg["sources"] if s.get("enabled", True)}
    candidates, seen = [], set()
    for item in entries:
        source = sources[item["source"]]
        if not item["url"].startswith("https://"):
            raise ValueError("Catch-up requires explicit HTTPS job URLs")
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        job = Job(item["id"], item["title"], source["name"], item["location"], item["url"], source=source["name"])
        job, opened = enrich_job(job)
        score_job(job, int(source.get("priority", 0)))
        if opened and is_candidate(job, int(cfg.get("filters", {}).get("min_score", 50))):
            candidates.append(job)
            log.info("Eligible: %s — %s (%s)", job.company, job.title, job.score)
        else:
            log.info("Skipped: closed, unavailable or fails current filters: %s", job.title)
    log.info("Targeted catch-up: %d of %d reviewed jobs eligible", len(candidates), len(entries))
    if dry_run:
        return candidates
    token, chat = telegram_credentials()
    if not token or not chat:
        raise ValueError("Job bot credentials are missing; nothing sent")
    notify_jobs(token, chat, candidates)
    storage = Storage(cfg["db_path"])
    for job in candidates:
        storage.mark_seen(job)
    storage.conn.close()
    log.info("Targeted catch-up delivered successfully: %d job messages", len(candidates))
    return candidates


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_catchup(args.manifest, args.dry_run)
