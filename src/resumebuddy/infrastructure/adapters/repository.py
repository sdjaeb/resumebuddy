import json
import os
from resumebuddy.domain.models import UserProfile
from resumebuddy.ports.repository import IProfileRepository

class FileSystemProfileRepository(IProfileRepository):
    def save_profile(self, profile: UserProfile, path: str):
        with open(path, "w") as f:
            f.write(profile.model_dump_json(indent=2))

    def load_profile(self, path: str) -> UserProfile:
        if not os.path.exists(path):
            return UserProfile()
        with open(path, "r") as f:
            data = json.load(f)
            return UserProfile(**data)
