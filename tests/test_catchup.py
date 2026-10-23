from hwjobradar import main
from hwjobradar.models import Job
from hwjobradar.storage import Storage


def test_catchup_sends_existing_then_normal_run_skips(monkeypatch, tmp_path):
    path = str(tmp_path / "seen.db")
    job = Job("known", "RTL Student", "Test", "Israel", "https://example.com/job")
    store = Storage(path)
    store.mark_seen(job)
    store.conn.close()
    monkeypatch.setattr(main, "load_config", lambda _: {"db_path": path, "sources": [{"name": "Test", "type": "test"}]})
    monkeypatch.setattr(main, "telegram_credentials", lambda: ("test", "test"))
    monkeypatch.setattr(main, "fetch_source", lambda _: [job])
    monkeypatch.setattr(main, "enrich_job", lambda j: (j, True))
    monkeypatch.setattr(main, "score_job", lambda j, _: setattr(j, "score", 100))
    monkeypatch.setattr(main, "is_candidate", lambda *_: True)
    sent = []
    monkeypatch.setattr(main, "notify_jobs", lambda token, chat, jobs: sent.extend(jobs))
    main.run(include_seen=True)
    assert sent == [job]
    sent.clear()
    main.run()
    assert sent == []
