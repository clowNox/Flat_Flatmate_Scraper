import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_GROUP_URL = os.getenv("TARGET_GROUP_URL", "https://www.facebook.com/groups/your_target_group_id")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "ulivio_leads.csv")

# Scraping configuration
SCROLL_PAUSE_TIME = 3  # Seconds to wait after scrolling
MAX_POSTS_TO_SCAN = 100 # Safety limit
DAYS_TO_LOOK_BACK = 7  # Scan posts from the last 7 days

# OpenAI System Prompt for structuring
OPENAI_SYSTEM_PROMPT = """
You are an AI assistant for U-livio, extracting structured lead data from messy Facebook housing group posts (like Flat & Flatmates).
Given the raw text of a Facebook post, extract the following fields in JSON format:
- "flat_size": e.g., "1 BHK", "2 BHK", "Private Room", "Preoccupied Bed", "Shared Room". If not found, output null.
- "location": The specific area, neighborhood, or city mentioned. If not found, output null.
- "furnishing_status": e.g., "Fully Furnished", "Semi Furnished", "Unfurnished". If not found, output null.
- "rent": The rent amount and currency (e.g., "15000 INR", "20k"). If not found, output null.
- "contact_details": Any phone numbers, whatsapp numbers, or email addresses found. If not found, output null.
- "intent": "Offering" (they have a place) or "Looking" (they need a place). If unsure, output "Unknown".

Return ONLY the raw JSON object, without any markdown formatting, backticks, or extra text.
"""

# Selectors (Note: Facebook changes these frequently, these might need updates)
SELECTORS = {
    "post_container": "div[role='feed'] > div",
    "post_author": "strong",
    "post_text": "div[dir='auto']",
    "post_date": "span > a[role='link'] > span, span > a[role='link'] > abbr"
}
