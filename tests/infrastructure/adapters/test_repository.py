import os
import pytest
import json
from resumebuddy.domain.models import UserProfile
from resumebuddy.infrastructure.adapters.repository import FileSystemProfileRepository

def test_file_system_profile_repository_save_load(tmp_path):
    repo = FileSystemProfileRepository()
    profile_path = os.path.join(tmp_path, "test_profile.json")
    profile = UserProfile(min_salary=150000)
    
    repo.save_profile(profile, profile_path)
    assert os.path.exists(profile_path)
    
    loaded = repo.load_profile(profile_path)
    assert loaded.min_salary == 150000

def test_file_system_profile_repository_load_default(tmp_path):
    repo = FileSystemProfileRepository()
    profile_path = os.path.join(tmp_path, "non_existent.json")
    
    loaded = repo.load_profile(profile_path)
    assert isinstance(loaded, UserProfile)
    assert loaded.min_salary == 130000 # Default value
