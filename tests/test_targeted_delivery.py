import yaml
import pytest
from hwjobradar import catchup
from hwjobradar.storage import Storage


def setup(monkeypatch,tmp_path):
    cfg = {"db_path":str(tmp_path/"seen.db"),"sources":[{"name":"Test","priority":12}],"filters":{"min_score":50}}
    monkeypatch.setattr(catchup,"load_config",lambda:cfg)
    entries = [{"id":"wanted","title":"FPGA Intern","source":"Test","location":"Israel","url":"https://example.com/wanted"},
               {"id":"blocked","title":"SoC Power Analysis Engineer","source":"Test","location":"Israel","url":"https://example.com/blocked"}]
    path=tmp_path/"manifest.yaml"
    path.write_text(yaml.safe_dump({"jobs":entries}))
    called=[]
    def enrich(j):
        called.append(j.id)
        j.description="FPGA RTL verification. BSc Electrical Engineering."
        return j,True
    monkeypatch.setattr(catchup,"enrich_job",enrich)
    monkeypatch.setattr(catchup,"telegram_credentials",lambda:('test','test'))
    sent=[]
    monkeypatch.setattr(catchup,"notify_jobs",lambda token,chat,jobs:sent.extend(jobs))
    return cfg,path,called,sent


def test_targeted_delivery_only_sends_explicit_eligible_jobs(monkeypatch,tmp_path):
    cfg,path,called,sent=setup(monkeypatch,tmp_path)
    result=catchup.run_catchup(path)
    assert called==['wanted','blocked']
    assert [j.id for j in sent]==['wanted']
    assert result==sent
    store=Storage(cfg['db_path'])
    assert store.seen('wanted')
    assert not store.seen('blocked')


def test_targeted_preview_does_not_send_or_write_history(monkeypatch,tmp_path):
    cfg,path,called,sent=setup(monkeypatch,tmp_path)
    assert len(catchup.run_catchup(path,dry_run=True))==1
    assert sent==[]
    from pathlib import Path
    assert not Path(cfg['db_path']).exists()


def test_empty_targeted_list_does_not_fall_back_to_full_scan(monkeypatch,tmp_path):
    cfg,path,called,sent=setup(monkeypatch,tmp_path)
    path.write_text('jobs: []')
    with pytest.raises(ValueError,match='empty'):
        catchup.run_catchup(path)
    assert called==[] and sent==[]
