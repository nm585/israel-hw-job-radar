from hwjobradar.main import run


def setup_scan(monkeypatch,tmp_path,names,failed):
    alerts=[]
    sources=[{'name':n,'type':'test'} for n in names]
    monkeypatch.setattr('hwjobradar.main.load_config',lambda _: {'db_path':str(tmp_path/'seen.db'),'sources':sources})
    monkeypatch.setattr('hwjobradar.main.telegram_credentials',lambda: ('main','chat'))
    monkeypatch.setattr('hwjobradar.main.health_credentials',lambda: ('health','other'))
    def fetch(src):
        if src['name'] in failed: raise RuntimeError('Source unavailable')
        return []
    monkeypatch.setattr('hwjobradar.main.fetch_source',fetch)
    monkeypatch.setattr('hwjobradar.main.notify_text',lambda token,chat,text:alerts.append((token,text)))
    return alerts


def test_single_source_outage_never_alerts_main_and_recovery_uses_health(monkeypatch,tmp_path):
    failed={'CEVA'}
    alerts=setup_scan(monkeypatch,tmp_path,['CEVA','Intel','NVIDIA'],failed)
    run(); assert alerts==[]
    run(); assert [a[0] for a in alerts]==['health']
    run(); assert len(alerts)==1
    failed.clear();run();assert [a[0] for a in alerts]==['health','health']


def test_nvidia_outage_and_recovery_only_use_support_bot(monkeypatch,tmp_path):
    failed={'NVIDIA'}
    alerts=setup_scan(monkeypatch,tmp_path,['NVIDIA','Intel','CEVA'],failed)
    run(); assert alerts==[]
    run(); assert [a[0] for a in alerts]==['health']
    failed.clear(); run()
    assert [a[0] for a in alerts]==['health','health']


def test_major_outage_alerts_main_once_and_recovers(monkeypatch,tmp_path):
    failed={'Intel','CEVA'}
    alerts=setup_scan(monkeypatch,tmp_path,['NVIDIA','Intel','CEVA'],failed)
    run();run();run()
    main=[t for dest,t in alerts if dest=='main'];assert len(main)==1 and '2 מתוך 3' in main[0]
    failed.clear();run();assert len([t for dest,t in alerts if dest=='main'])==2


def test_dry_run_does_not_send_health_alerts(monkeypatch,tmp_path):
    alerts=setup_scan(monkeypatch,tmp_path,['NVIDIA'],{'NVIDIA'})
    run(dry_run=True);run(dry_run=True);assert alerts==[]


def test_health_delivery_failure_does_not_abort_scanning(monkeypatch,tmp_path):
    setup_scan(monkeypatch,tmp_path,['NVIDIA','Intel','CEVA'],{'CEVA'})
    def fail(*args):raise RuntimeError('Delivery failed')
    monkeypatch.setattr('hwjobradar.main.notify_text',fail)
    run();run()
