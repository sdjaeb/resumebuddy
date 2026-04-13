from typing import List, Dict, Any
from .models import UserProfile

class DomainService:
    @staticmethod
    def filter_jobs_by_preferences(jobs: List[Dict[str, Any]], profile: UserProfile) -> List[Dict[str, Any]]:
        """
        Pure domain logic to filter jobs based on profile preferences.
        Currently handles company exclusions and basic keyword matches if needed.
        """
        filtered = []
        for job in jobs:
            company = job.get('company', '').lower()
            if any(dq.lower() in company for dq in profile.disqualified_companies):
                continue
            filtered.append(job)
        return filtered
