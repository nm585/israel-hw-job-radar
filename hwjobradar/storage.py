import sqlite3
from pathlib import Path
from datetime import datetime, timezone


class Storage:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id TEXT PRIMARY KEY,
                first_seen TEXT NOT NULL,
                title TEXT,
                company TEXT,
                url TEXT,
                last_score INTEGER
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_health (
                source TEXT PRIMARY KEY,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                alerted INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def seen(self, job_id: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM seen_jobs WHERE id=?", (job_id,))
        return cur.fetchone() is not None

    def mark_seen(self, job) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT OR IGNORE INTO seen_jobs(id, first_seen, title, company, url, last_score) VALUES(?,?,?,?,?,?)",
            (job.id, now, job.title, job.company, job.url, job.score),
        )
        self.conn.commit()

    def record_success(self, source: str) -> bool:
        """Returns True if the source recovered from an alerted outage."""
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "SELECT alerted FROM source_health WHERE source=?", (source,)
        ).fetchone()
        recovered = bool(row and row[0])
        self.conn.execute(
            "INSERT INTO source_health(source,consecutive_failures,alerted,updated_at) VALUES(?,0,0,?) "
            "ON CONFLICT(source) DO UPDATE SET consecutive_failures=0, alerted=0, updated_at=excluded.updated_at",
            (source, now),
        )
        self.conn.commit()
        return recovered

    def record_failure(self, source: str, threshold: int = 2) -> bool:
        """Returns True only when this failure crosses the alert threshold."""
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "SELECT consecutive_failures, alerted FROM source_health WHERE source=?", (source,)
        ).fetchone()
        failures, alerted = row if row else (0, 0)
        failures += 1
        should_alert = failures >= threshold and not alerted
        new_alerted = 1 if (alerted or should_alert) else 0
        self.conn.execute(
            "INSERT INTO source_health(source,consecutive_failures,alerted,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(source) DO UPDATE SET consecutive_failures=excluded.consecutive_failures, alerted=excluded.alerted, updated_at=excluded.updated_at",
            (source, failures, new_alerted, now),
        )
        self.conn.commit()
        return should_alert
