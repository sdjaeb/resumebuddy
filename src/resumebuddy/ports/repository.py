from abc import ABC, abstractmethod
from resumebuddy.domain.models import UserProfile

class IProfileRepository(ABC):
    @abstractmethod
    def save_profile(self, profile: UserProfile, path: str):
        pass  # pragma: no cover

    @abstractmethod
    def load_profile(self, path: str) -> UserProfile:
        pass  # pragma: no cover
