# Facebook Group Scraper

A headless/headful browser scraper built with Playwright and Python to extract lead data from Facebook housing groups (like Flat & Flatmates). It uses the OpenAI API to structure messy post text into clean data (rent, flat size, location, etc.) for U-livio's growth pipeline.

## Setup Instructions

1. **Activate Environment:** Ensure you are in the virtual environment.
   ```bash
   source venv/bin/activate
   ```

2. **Configuration:**
   - Open `.env` and paste your `OPENAI_API_KEY`.
   - Set the `TARGET_GROUP_URL` to the specific Facebook group you want to scrape.
   - (Optional) Change the `OUTPUT_FILE` name.

3. **Running the Scraper:**
   ```bash
   python main.py
   ```

## First Run (Authentication)

The first time you run `main.py`, a browser window will open and navigate to Facebook. You will be given **15 seconds** to manually log in to your account.
- **IMPORTANT:** Use a secondary/burner account. Scraping violates Facebook's Terms of Service and can result in bans.
- Once you log in, Playwright will save your session cookies into the `playwright_profile/` directory.
- On subsequent runs, you will not need to log in again; Playwright will load the saved session automatically.

## How it Works
1. Navigates to the group.
2. Scrolls down to load posts.
3. Extracts the post author, date, and raw text.
4. If an OpenAI API key is provided, it sends the raw text to ChatGPT to extract structured fields (`flat_size`, `location`, `rent`, `furnishing_status`, `intent`, `contact_details`).
5. Saves the results to a CSV file (e.g., `ulivio_leads.csv`).
