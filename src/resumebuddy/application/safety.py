import re
import logging

class SafetyMiddleware:
    """
    Redacts PII (Emails, Phone Numbers) from AI-generated text.
    Ensures that generated content is safe for public/sharing contexts.
    """
    
    # Simple regex for demonstration (In production, use Presidio/GLiNER)
    EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    PHONE_PATTERN = r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4})'

    @classmethod
    def scrub_text(cls, text: str) -> str:
        scrubbed = re.sub(cls.EMAIL_PATTERN, "[REDACTED_EMAIL]", text)
        scrubbed = re.sub(cls.PHONE_PATTERN, "[REDACTED_PHONE]", scrubbed)
        
        if "[REDACTED" in scrubbed:
            logging.info("SafetyMiddleware: PII detected and redacted.")
            
        return scrubbed
