from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml


def schedules():
    return yaml.load(Path('.github/workflows/job-alerts.yml').read_text(), Loader=yaml.BaseLoader)['on']['schedule']


def values(field, limit):
    if field == "*":
        return set(range(limit))
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
        for h in values(hour, 24):
            for m in values(minute, 60):
                actual[h * 60 + m] += 1
    assert set(actual) == set(range(7, 1440, 10))
    assert len(actual) == 144
    assert all(v == 1 for v in actual.values())


def test_utc_mapping_including_dst_transition_days():
    # Validate local-time membership across DST. This models clock slots, not
    # guaranteed GitHub executions, which may be delayed/skipped by the service.
    zone = ZoneInfo('Asia/Jerusalem')
    for date, expected in [((2026,1,15),144), ((2026,7,15),144),
                           ((2026,3,27),138), ((2026,10,25),150)]:
        start = datetime(*date, tzinfo=zone)
        end = start + timedelta(days=1)
        instant = start.astimezone(timezone.utc)
        found = []
        while instant < end.astimezone(timezone.utc):
            local = instant.astimezone(zone)
            for item in schedules():
                minute, hour, *_ = item['cron'].split()
                if local.hour in values(hour,24) and local.minute in values(minute,60):
                    found.append(instant)
            instant += timedelta(minutes=1)
        assert len(found) == expected
        assert all(b-a == timedelta(minutes=10) for a,b in zip(found,found[1:]))
