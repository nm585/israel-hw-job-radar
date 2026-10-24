from hwjobradar.models import Job
from hwjobradar.fetchers import enrich_job
from hwjobradar.scoring import allows_no_prior_experience


def test_workday_uses_real_requirements_instead_of_empty_html(monkeypatch):
    class Response:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {'jobPostingInfo': {'jobDescription': '<p>Requires 4 years of experience.</p>'}}
    def get(url, **kwargs):
        assert url == 'https://marvell.wd1.myworkdayjobs.com/wday/cxs/marvell/MarvellCareers/job/Israel/Intern_123'
        return Response()
    monkeypatch.setattr('hwjobradar.fetchers.requests.get', get)
    j = Job('x','Verification Intern','Marvell','Israel','https://marvell.wd1.myworkdayjobs.com/en-US/MarvellCareers/job/Israel/Intern_123')
    j, opened = enrich_job(j)
    assert opened
    assert '4 years' in j.description
    assert not allows_no_prior_experience(j)
