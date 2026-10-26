from hwjobradar.models import Job
from hwjobradar.main import run


def test_hebrew_student_title_reaches_detail_page_before_score_filter(monkeypatch,tmp_path):
    j = Job('student','סטודנט','Example','Israel','https://example.com/job')
    monkeypatch.setattr('hwjobradar.main.load_config',lambda _: {'db_path':str(tmp_path/'seen.db'),'sources':[{'type':'test','name':'Example'}]})
    monkeypatch.setattr('hwjobradar.main.telegram_credentials',lambda: ('',''))
    monkeypatch.setattr('hwjobradar.main.fetch_source',lambda _: [j])
    called = []
    def enrich(item):
        called.append(item.id)
        item.description = 'ASIC RTL verification and FPGA. Student role.'
        return item, True
    monkeypatch.setattr('hwjobradar.main.enrich_job',enrich)
    result = run(dry_run=True)
    assert called == ['student']
    assert result == [j]

def test_generic_engineer_title_reaches_parttime_requirements(monkeypatch,tmp_path):
    j = Job('partial','Hardware Engineer','Example','Israel','https://example.com/job')
    monkeypatch.setattr('hwjobradar.main.load_config',lambda _: {'db_path':str(tmp_path/'partial.db'),'sources':[{'type':'test','name':'Example'}]})
    monkeypatch.setattr('hwjobradar.main.telegram_credentials',lambda: ('',''))
    monkeypatch.setattr('hwjobradar.main.fetch_source',lambda _: [j])
    def enrich(item):
        item.description = 'Part-time position. ASIC RTL verification and FPGA.'
        return item, True
    monkeypatch.setattr('hwjobradar.main.enrich_job',enrich)
    assert run(dry_run=True) == [j]
