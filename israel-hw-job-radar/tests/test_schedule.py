from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml


def schedules():
    # BaseLoader retains YAML's 'on' key as a string.
    return yaml.load(Path('.github/workflows/job-alerts.yml').read_text(), Loader=yaml.BaseLoader)['on']['schedule']


def values(field):
    result = set()
    for part in field.split(','):
        if '-' in part:
            a, b = map(int, part.split('-'))
            result.update(range(a, b + 1))
        else:
            result.add(int(part))
    return result


def test_exact_daily_slots_no_extras_or_duplicates():
    actual = Counter()
    for item in schedules():
        assert item['timezone'] == 'Asia/Jerusalem'
        minute, hour, *rest = item['cron'].split()
        assert rest == ['*', '*', '*']
        for h in values(hour):
            for m in values(minute):
                actual[h * 60 + m] += 1
    expected = set(range(8 * 60 + 31, 23 * 60 + 2, 15)) | {23 * 60 + 31, 1}
    assert set(actual) == expected
    assert len(actual) == 61
    assert all(v == 1 for v in actual.values())


def test_utc_mapping_including_dst_transition_days():
    zone = ZoneInfo('Asia/Jerusalem')
    for date in [(2026,1,15),(2026,7,15),(2026,3,27),(2026,10,25)]:
        start = datetime(*date, tzinfo=zone)
        end = start + timedelta(days=1)
        instant = start.astimezone(timezone.utc)
        found=[]
        while instant < end.astimezone(timezone.utc):
            local=instant.astimezone(zone)
            for item in schedules():
                minute,hour,*_ = item['cron'].split()
                if local.hour in values(hour) and local.minute in values(minute):
                    found.append((local.hour,local.minute))
            instant += timedelta(minutes=1)
        assert len(found)==61
        assert len(set(found))==61
        assert (8,31) in found and (23,1) in found and (23,31) in found and (0,1) in found
