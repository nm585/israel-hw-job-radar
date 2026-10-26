import json
import pytest
from hwjobradar.models import Job
from hwjobradar.fetchers import apple_hydration, embedded_comeet_json, comeet_description, fetch_workday, enrich_job
from hwjobradar.scoring import allows_no_prior_experience, score_job, is_candidate


@pytest.mark.parametrize('text', [
    'BSc student with at least 2 years remaining until graduation.',
    'At least 4 semesters (2 years) left before graduation.',
    'Masters students should have at least 1.5 years of their studies still remaining.',
    'B.Sc. student in Software Engineering with 2+ years left.',
    'Ability to complete a 12 month internship.',
])
def test_study_duration_is_not_prior_work_experience(text):
    job = Job('x', 'Hardware Intern', 'Example', 'Israel', 'https://example.com', description=text)
    assert allows_no_prior_experience(job)
    job.description += ' Minimum 4 years of professional experience required.'
    assert not allows_no_prior_experience(job)


def test_intel_location_facet_filters_before_worldwide_limit(monkeypatch):
    calls = []
    class Response:
        headers = {'content-type':'application/json'}
        def __init__(self, value): self.value = value
        def raise_for_status(self): pass
        def json(self): return self.value
    class Session:
        headers = {}
        def post(self, url, json, **kwargs):
            calls.append(json)
            if not json['appliedFacets']:
                return Response({'total':791,'facets':[{'facetParameter':'locationMainGroup','values':[{'facetParameter':'locations','values':[{'descriptor':'Israel, Haifa','id':'haifa'},{'descriptor':'PETAH TIKVA','id':'ptk'},{'descriptor':'US, Santa Clara','id':'us'}]}]}]})
            assert json['appliedFacets'] == {'locations':['haifa','ptk']}
            return Response({'total':1,'jobPostings':[{'title':'RTL Student','locationsText':'Israel, Haifa','externalPath':'/job/Israel/Student_123'}]})
    monkeypatch.setattr('hwjobradar.fetchers.requests.Session', Session)
    assert len(fetch_workday({'tenant':'intel','dc':'wd1','site':'External'})) == 1


def test_apple_reads_real_qualifications_and_all_locations(monkeypatch):
    data = {'loaderData':{'jobDetails':{'jobsData':{'postingTitle':'Hardware Engineering Student','description':'Hardware engineering and FPGA','minimumQualifications':'BSc student in EE','preferredQualifications':'Python is an advantage','teamNames':['Hardware','Students'],'locations':[{'name':'Herzliya'},{'name':'Haifa'}]}}}}
    html = '<script>window.__staticRouterHydrationData = JSON.parse(' + json.dumps(json.dumps(data)) + ');</script>'
    assert apple_hydration(html) == data
    class Response:
        status_code = 200
        text = html
    monkeypatch.setattr('hwjobradar.fetchers.requests.get',lambda *a,**kw:Response())
    job = Job('apple','Hardware Engineering Student','Apple','Jerusalem','https://jobs.apple.com/en-il/details/200676938')
    job, opened = enrich_job(job)
    assert opened and 'BSc student' in job.description and 'Python' in job.description
    assert job.location == 'Herzliya; Haifa'
    score_job(job, 12)
    assert is_candidate(job)


def test_comeet_embedded_positions_preserve_requirements():
    value = [{'name':'Verification Student','custom_fields':{'details':[{'name':'Requirements','value':'<p>Minimum 4 years of experience</p>'}]}}]
    html = '<script>var COMPANY_POSITIONS_DATA; COMPANY_POSITIONS_DATA = ' + json.dumps(value) + ';</script>'
    positions = embedded_comeet_json(html, 'COMPANY_POSITIONS_DATA')
    text = comeet_description(positions[0])
    job = Job('x','Verification Student','Example','Israel','https://example.com',description=text)
    assert not allows_no_prior_experience(job)


def test_signal_integrity_intern_is_in_hardware_scope():
    job = Job('x','Signal Integrity Intern','Marvell','Yokneam','https://example.com',description='BSc student in Electrical Engineering. Signal integrity simulation and lab measurements.')
    score_job(job,12)
    assert is_candidate(job)
