import asyncio
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from playwright.async_api import async_playwright
import openai

from config import (
    OPENAI_API_KEY, TARGET_GROUP_URL, OUTPUT_FILE, 
    SCROLL_PAUSE_TIME, MAX_POSTS_TO_SCAN, DAYS_TO_LOOK_BACK,
    OPENAI_SYSTEM_PROMPT, SELECTORS
)

client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def parse_post_with_ai(post_text):
    if not client or not post_text:
        return {}
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # or gpt-4
            messages=[
                {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract structured data from this post:\n\n{post_text}"}
            ],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        # Clean up in case the model returns markdown JSON blocks
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing post with AI: {e}")
        return {}

def is_within_timeframe(date_text):
    # This is a heuristic. Facebook dates are like "2 hrs", "Yesterday", "October 12", "October 12, 2022"
    # For a robust scraper, you'd use a date parsing library like dateparser.
    # Here we simplify for demonstration purposes.
    if not date_text: return True
    date_text = date_text.lower()
    if any(x in date_text for x in ["m", "h", "hr", "hrs", "min", "mins", "just now", "yesterday"]):
        return True # Within a day
    
    # If it contains a year less than current year, it's old
    current_year = str(datetime.now().year)
    if any(str(year) in date_text for year in range(2000, int(current_year))):
        return False
        
    return True # We assume it's recent if it just says "October 12" (meaning this year). Real impl requires more robust parsing.

async def main():
    if TARGET_GROUP_URL == "https://www.facebook.com/groups/your_target_group_id":
        print("Please set your TARGET_GROUP_URL in the .env file.")
        return

    async with async_playwright() as p:
        # User Data Directory to save login session cookies
        user_data_dir = os.path.join(os.getcwd(), 'playwright_profile')
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Run headed so user can login manually if needed
            viewport={"width": 1280, "height": 720}
        )
        
        page = await browser_context.new_page()
        print("Navigating to Facebook...")
        await page.goto("https://www.facebook.com/")
        
        # Give user time to log in if they aren't already
        print("Waiting 15 seconds to ensure you are logged in...")
        print("If you are not logged in, please log in manually now. The session will be saved for future runs.")
        await page.wait_for_timeout(15000)

        print(f"Navigating to target group: {TARGET_GROUP_URL}")
        await page.goto(TARGET_GROUP_URL)
        await page.wait_for_timeout(5000)

        posts_data = []
        extracted_texts = set() # To avoid duplicates
        
        last_height = await page.evaluate("document.body.scrollHeight")
        
        print("Scanning posts...")
        for _ in range(MAX_POSTS_TO_SCAN // 5): # rough estimate of scroll actions
            # Get posts on current view
            post_elements = await page.query_selector_all(SELECTORS["post_container"])
            
            for post in post_elements:
                try:
                    text_el = await post.query_selector(SELECTORS["post_text"])
                    author_el = await post.query_selector(SELECTORS["post_author"])
                    date_el = await post.query_selector(SELECTORS["post_date"])
                    
                    post_text = await text_el.inner_text() if text_el else ""
                    post_author = await author_el.inner_text() if author_el else "Unknown"
                    post_date = await date_el.inner_text() if date_el else ""
                    
                    if not post_text or post_text in extracted_texts:
                        continue
                    
                    extracted_texts.add(post_text)
                    
                    # Check time frame
                    if not is_within_timeframe(post_date):
                        print(f"Encountered older post from {post_date}. Stopping scan.")
                        break
                    
                    print(f"Extracting post by {post_author}...")
                    
                    # Structure with AI
                    structured_data = parse_post_with_ai(post_text)
                    
                    posts_data.append({
                        "Author": post_author,
                        "Date": post_date,
                        "Flat Size": structured_data.get("flat_size"),
                        "Location": structured_data.get("location"),
                        "Rent": structured_data.get("rent"),
                        "Furnishing": structured_data.get("furnishing_status"),
                        "Intent": structured_data.get("intent", "Unknown"),
                        "Contact": structured_data.get("contact_details"),
                        "Raw Text": post_text
                    })
                    
                except Exception as e:
                    print(f"Error processing a post: {e}")
                    
            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(SCROLL_PAUSE_TIME * 1000)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("Reached the bottom or no more posts loaded.")
                break
            last_height = new_height
            
        print(f"Extraction complete. Found {len(posts_data)} relevant posts.")
        
        if posts_data:
            df = pd.DataFrame(posts_data)
            df.to_csv(OUTPUT_FILE, index=False)
            print(f"Data saved to {OUTPUT_FILE}")
        else:
            print("No data extracted.")
            
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(main())
