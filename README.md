# Web-Scraper

This project is a powerful web scraping tool designed to scrape and parse both static and dynamic webpages, as well as PDF documents. It processes the scraped data to generate concise summaries, including headlines and press releases, with specific functionality for handling Congress-related websites that deliver status updates on bills.

---

## Features

### 1. Scraping Capabilities
- **Static Webpages**: Utilizes `requests` and `BeautifulSoup` to scrape and parse static HTML content.
- **Dynamic Webpages**: Leverages `playwright` to handle JavaScript-rendered content effectively.
- **PDF Documents**: Extracts text from PDF files using `pdfplumber`.

### 2. Summarization
- The scraped text is summarized into:
  - A **headline**
  - A **press release**
- Powered by OpenAI's API for advanced language processing and summarization.

### 3. Congress Bill Detection
- **Bill Status Updates**: For pages like [Congress.gov](https://www.congress.gov/bill/118th-congress/house-bill/10564/text/ih?format=txt), the scraper detects whether the bill text has been uploaded to the page.
  - If the bill is **not yet available**, it logs the data into a separate CSV file.
  - If the bill is available, it processes the text and outputs the summaries into the main output CSV file.

---

## Installation

To run this web scraper, you will need the following dependencies:

```bash
pip install csv
pip install openai
pip install pdfplumber
pip install requests
pip install beautifulsoup4
pip install playwright
```

> Note: Ensure Playwright is installed and properly set up by running:
> ```bash
> playwright install
> ```

---

## Usage

1. Clone this repository:

2. Update the configuration settings in the script (e.g., target URLs, API keys).

3. Run the script:
   ```bash
   python webscraper.py
   ```

4. Outputs:
   - **finishedMessages CSV File**: Contains summaries for pages where the data was successfully scraped and processed.
   - **unavailable CSV File**: Contains entries for pages where the desired content (e.g., bill text) was not yet uploaded.

---

## How It Works

### Core Libraries Used:
- **CSV**: For structured storage of scraped and processed data.
- **OpenAI**: Summarizes the scraped text into readable formats.
- **PDFPlumber**: Extracts and processes text from PDF documents.
- **Requests and BeautifulSoup**: Fetches and parses static webpage content.
- **Playwright**: Handles dynamic webpages that require JavaScript rendering.

### Workflow:
1. **Fetch Data**: Depending on the type of content (static HTML, dynamic content, or PDF), the appropriate library is used to fetch and parse the data.
2. **Summarize Content**: Scraped content is processed using OpenAI to generate clear and concise summaries.
3. **Categorize Data**:
   - If specific content (like a bill's text) is unavailable, the URL and metadata are logged into a separate CSV file.
   - Processed data is stored in the main output CSV file.

---

## Example Output

### Input:
**Target URL**: [Congress.gov Bill Text](https://www.congress.gov/bill/118th-congress/house-bill/10564/text/ih?format=txt)

### Output:
- **Headline**: "House Bill 10564 Introduced to Address Infrastructure Improvements"
- **Press Release**: "The House Bill 10564, introduced in the 118th Congress, aims to improve the nation's infrastructure through innovative funding and development strategies."

If the bill text is unavailable:
- Logged to `unavailable.csv` with metadata for later processing.

---

## Acknowledgments

- [OpenAI](https://openai.com) for its powerful API.
- [Playwright](https://playwright.dev) for handling dynamic content.
- [Congress.gov](https://www.congress.gov) for providing publicly accessible legislative information.
