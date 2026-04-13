import json
import os
import typer
from .models import UserProfile

PROFILE_PATH = "user_profile.json"

class ProfileManager:
    @staticmethod
    def save_profile(profile: UserProfile, path: str = PROFILE_PATH):
        with open(path, "w") as f:
            f.write(profile.model_dump_json(indent=2))
        print(f"[bold green]Profile saved to {path}[/bold green]")

    @staticmethod
    def load_profile(path: str = PROFILE_PATH) -> UserProfile:
        if not os.path.exists(path):
            return UserProfile() # return default profile
        with open(path, "r") as f:
            data = json.load(f)
            return UserProfile(**data)

    @staticmethod
    def interactive_build() -> UserProfile:
        print("[bold blue]Job Search Profile Builder[/bold blue]")
        print("Press Enter to accept the sensible default for any field.\n")
        
        default_profile = UserProfile()
        
        def prompt_list(field_name: str, default_list: list) -> list:
            val = typer.prompt(f"{field_name} (comma-separated)", default=", ".join(default_list))
            return [x.strip() for x in val.split(",") if x.strip()]

        preferred_languages = prompt_list("Preferred Languages", default_profile.preferred_languages)
        supporting_languages = prompt_list("Supporting/Non-Primary Languages", default_profile.supporting_languages)
        learning_interests = prompt_list("Learning Interests", default_profile.learning_interests)
        
        role_preferences = typer.prompt("Role Preferences", default=default_profile.role_preferences)
        location = typer.prompt("Location & Remote Flex", default=default_profile.location)
        
        min_salary = typer.prompt("Minimum Salary (Hard floor)", type=int, default=default_profile.min_salary)
        target_salary = typer.prompt("Target Salary", type=int, default=default_profile.target_salary)
        
        growth_exceptions = typer.prompt("Growth Exceptions (for lower pay)", default=default_profile.growth_exceptions)
        industry_interests = typer.prompt("Industry Interests", default=default_profile.industry_interests)
        clearance = typer.prompt("Clearance Level", default=default_profile.clearance)
        
        disqualified_companies = prompt_list("Disqualified Companies", default_profile.disqualified_companies)
        recent_applications = prompt_list("Recent Applications", default_profile.recent_applications)

        profile = UserProfile(
            preferred_languages=preferred_languages,
            supporting_languages=supporting_languages,
            learning_interests=learning_interests,
            role_preferences=role_preferences,
            location=location,
            min_salary=min_salary,
            target_salary=target_salary,
            growth_exceptions=growth_exceptions,
            industry_interests=industry_interests,
            clearance=clearance,
            disqualified_companies=disqualified_companies,
            recent_applications=recent_applications
        )
        
        ProfileManager.save_profile(profile)
        return profile
