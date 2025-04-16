# Web-Scraper

This project is a robust web scraping and summarization pipeline tailored for legislative content. It can process static and dynamic webpages, as well as PDF documents, and outputs concise summaries—such as headlines and press releases—especially for bills hosted on Congress.gov. Summarized data is automatically inserted into a MySQL database.

---

## 📌 Features

### 🔍 Scraping Capabilities
- **Static Webpages**: Fetched with `requests` and parsed using `BeautifulSoup`.
- **Dynamic Webpages**: Rendered and extracted using `playwright` for JavaScript-heavy pages.
- **PDF Documents**: Handled using `pdfplumber` for direct text extraction.

### 🤖 AI-Powered Summarization
- Uses OpenAI's GPT API to generate:
  - News-style **headlines**
  - Detailed **press releases**
  - Cosponsor summaries with structured formatting

### 🧠 Legislative Awareness
- **Congress Bill Status Check**: For each bill URL, the scraper determines if the bill text has been published.
  - If yes → Summarizes content and inserts into the database.
  - If no → Adds to an invalid URLs CSV file for later review.

---

## 🛠 Installation

```bash
pip install -r requirements.txt
playwright install
```

### `requirements.txt` should include:

```
openai
pdfplumber
requests
beautifulsoup4
playwright
PyYAML
mysql-connector-python
```

---

## 🚀 Usage

1. **Prepare Your Input**  
   Populate `csv/house.csv` or `csv/senate.csv` with target URLs.

2. **Run the Scraper**  
   ```bash
   python main.py h     # For House URLs
   python main.py s     # For Senate URLs
   ```

3. **Results**  
   - Valid data will be inserted into the `tns.press_release` table.
   - Invalid or pending URLs will be saved back into the same input CSV.

---

## 🧬 How It Works

### 🔧 Code Breakdown

- `main.py`: Entry point that loads URLs, processes them, calls the OpenAI API, and saves output to the database.
- `url_processing.py`: Fetches text from URLs depending on type (static, dynamic, or PDF).
- `openai_api.py`: 
  - Builds prompts
  - Calls GPT API to summarize bills
  - Generates structured cosponsor summaries
- `db_insert.py`: Inserts headlines and press releases into the MySQL database (with source URL and timestamps).
- `configs/db_config.yml`: Contains DB connection credentials.

---

## 🗃️ Database Output

### Table: `tns.press_release`

Each entry includes:
- `headline`
- `content_date`
- `body_txt` (press release)
- `a_id` (House or Senate)
- `filename` (e.g., `$H billintroh-250314-hr101`)
- `source_url` (directly from the input)
- `status`, `create_date`, `last_action`, `uname`

---

## 🧪 Example

### Input:
`https://www.congress.gov/bill/119th-congress/house-bill/2906`

### Output in Database:
- **Headline**: "Rep. Johnson Introduces Rural Development Initiative Act"
- **Filename**: `$H billintroh-250314-hr2906`
- **Press Release**: Multi-paragraph summary with cosponsor list
- **Source URL**: Stored as a standalone column

If the bill text isn’t published yet, the URL will be logged in the original CSV file.

---

## 🧼 Cleanup & Logging

- URLs with missing content or parsing failures are deduplicated and logged.
- Script automatically avoids duplicate scraping and database insertions.
- CSV file of invalid links is overwritten each run.

---

## 📝 Known Issues / TODO

- [ ] Fix filename formatting bug when bill number or date is missing
- [ ] Handle odd formatting at the start of the year
- [ ] Prevent duplicate URL handling more aggressively
- [ ] Ensure OpenAI errors are fully logged and retry logic is considered

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) — GPT API for language understanding
- [Playwright](https://playwright.dev) — Dynamic webpage automation
- [Congress.gov](https://www.congress.gov) — Public legislative data
