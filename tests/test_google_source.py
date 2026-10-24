from hwjobradar.fetchers import parse_google_cards


def test_google_cards_use_actual_country_and_follow_next_page():
    html = '''<ul><li><h3>Hardware Intern</h3><span class="r0wTof">Tel Aviv, Israel</span><a href="jobs/results/123-intern?location=Israel"></a></li>
    <li><h3>Hardware Intern US</h3><span class="r0wTof">New York, USA</span><a href="jobs/results/456-intern?location=Israel"></a></li></ul>
    <a aria-label="Go to next page" href="?location=Israel&page=2"></a>'''
    jobs, next_page = parse_google_cards(html,'https://www.google.com/about/careers/applications/jobs/results/?location=Israel')
    assert len(jobs) == 1
    assert jobs[0].title == 'Hardware Intern'
    assert jobs[0].url == 'https://www.google.com/about/careers/applications/jobs/results/123-intern'
    assert next_page.endswith('location=Israel&page=2')
