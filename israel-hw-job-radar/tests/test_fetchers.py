from unittest.mock import Mock, patch

from hwjobradar.fetchers import fetch_ashby, fetch_html


def _resp(*, json_data=None, text="", content_type="text/html"):
    r = Mock()
    r.status_code = 200
    r.text = text
    r.headers = {"content-type": content_type}
    r.json.return_value = json_data
    r.raise_for_status.return_value = None
    return r


def test_ashby_filters_to_israel():
    payload = {
        "jobs": [
            {"id": "1", "title": "Hardware Intern", "location": "Tel Aviv, Israel", "jobUrl": "https://jobs.ashbyhq.com/x/1"},
            {"id": "2", "title": "Hardware Intern", "location": "Paris, France", "jobUrl": "https://jobs.ashbyhq.com/x/2"},
        ]
    }
    with patch("hwjobradar.fetchers.requests.get", return_value=_resp(json_data=payload)):
        jobs = fetch_ashby({"type": "ashby", "company": "x", "name": "X", "countries": ["Israel", "Tel Aviv"]})
    assert [j.id for j in jobs] == ["ab-x-1"]


def test_html_context_filters_global_page():
    html = """
    <html><body>
      <div class='job'><span>Tel Aviv, Israel</span><a href='/jobs/1'>FPGA Design Intern</a></div>
      <div class='job'><span>New York, USA</span><a href='/jobs/2'>FPGA Design Intern</a></div>
    </body></html>
    """
    with patch("hwjobradar.fetchers.requests.get", return_value=_resp(text=html)):
        jobs = fetch_html({
            "type": "html", "name": "X", "url": "https://example.com/careers",
            "base_url": "https://example.com", "href_regex": "/jobs/",
            "required_context_regex": "Israel|Tel Aviv", "default_location": "Israel"
        })
    assert len(jobs) == 1
    assert jobs[0].title == "FPGA Design Intern"
    assert jobs[0].url.endswith("/jobs/1")
