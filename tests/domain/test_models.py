from resumebuddy.domain.models import UserProfile

def test_user_profile_defaults():
    profile = UserProfile()
    assert "Python" in profile.preferred_languages
    assert profile.min_salary == 130000
    assert "Oracle" in profile.disqualified_companies
