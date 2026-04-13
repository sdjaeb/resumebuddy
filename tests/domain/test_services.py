from resumebuddy.domain.services import DomainService
from resumebuddy.domain.models import UserProfile

def test_filter_jobs_by_preferences():
    profile = UserProfile(disqualified_companies=["Oracle"])
    jobs = [
        {"company": "Google", "title": "SWE"},
        {"company": "Oracle", "title": "DBA"},
        {"company": "Amazon", "title": "SDE"}
    ]
    filtered = DomainService.filter_jobs_by_preferences(jobs, profile)
    assert len(filtered) == 2
    assert "Oracle" not in [j["company"] for j in filtered]
