from abc import ABC, abstractmethod
from typing import List, Optional
from resumebuddy.domain.models import UserProfile, JobOpportunity

class IProfileRepository(ABC):
    @abstractmethod
    def save_profile(self, profile: UserProfile, path: str):
        pass  # pragma: no cover

    @abstractmethod
    def load_profile(self, path: str) -> UserProfile:
        pass  # pragma: no cover

class IJobRepository(ABC):
    @abstractmethod
    def save_job(self, job: JobOpportunity):
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[JobOpportunity]:
        pass

    @abstractmethod
    def list_jobs(self) -> List[JobOpportunity]:
        pass

    @abstractmethod
    def update_status(self, job_id: str, status: str):
        pass
