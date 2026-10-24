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


def test_nested_country_facet_is_applied_before_pagination(monkeypatch):
    from hwjobradar.fetchers import fetch_workday
    class Response:
        headers = {'content-type': 'application/json'}
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data
    class Session:
        headers = {}
        def post(self, url, json, **kwargs):
            if not json['appliedFacets']:
                return Response({'total': 2000, 'facets': [{'facetParameter':'locationMainGroup','values':[{'facetParameter':'locationHierarchy1','values':[{'descriptor':'Israel','id':'israel-id'}]}]}]})
            assert json['appliedFacets'] == {'locationHierarchy1':['israel-id']}
            return Response({'total':1,'jobPostings':[{'title':'RTL Engineer','externalPath':'/job/Israel/RTL_123','locationsText':'Israel, Tel Aviv'}]})
    monkeypatch.setattr('hwjobradar.fetchers.requests.Session',Session)
    jobs = fetch_workday({'tenant':'test','dc':'wd1','site':'Careers'})
    assert len(jobs) == 1
