import csv
import requests
import pdfplumber
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

arr = []      # Holds normalized URLs to process
pdfs = []     # Holds PDFs only
invalidArr = []

# Shared browser/session variables
_browser = None
_context = None
_page = None


def add_invalid_url(url):
    cleaned_url = url.strip().rstrip('/').replace("/cosponsors", "").replace("/text", "")
    if cleaned_url not in invalidArr:
        invalidArr.append(cleaned_url)


def getUrls(input_csv):
    """Loads URLs from the specified CSV file, normalizes and deduplicates them."""
    global arr, pdfs, invalidArr
    seen = set()

    try:
        with open(input_csv, 'r', encoding='utf-8') as urls:
            reader = csv.reader(urls)
            for row in reader:
                url = row[0].strip().rstrip('/')
                if 'congress.gov' in url and not url.endswith('/text'):
                    url += '/text'

                canonical = url.replace('/cosponsors', '').replace('/text', '')
                if canonical in seen:
                    continue
                seen.add(canonical)

                if 'pdf' in url.lower():
                    pdfs.append(url)
                else:
                    arr.append(url)
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")

def getStaticUrlText(url):
    """Extracts text from a static URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        if "has not been received" in soup.get_text():
            add_invalid_url(url)
            return None
        else:
            return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL content: {e}")
        return None


def init_browser():
    """Initialize a reusable Playwright browser and context."""
    global _browser, _context, _page
    p = sync_playwright().start()
    _browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    _context = _browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        java_script_enabled=True
    )
    _page = _context.new_page()


def close_browser():
    """Closes the reusable browser session."""
    global _browser, _context, _page
    if _context:
        _context.close()
    if _browser:
        _browser.close()
    _browser = None
    _context = None
    _page = None


def getDynamicUrlText(url):
    """Uses a shared Playwright browser session to fetch dynamic page content."""
    global _page
    if _page is None:
        raise RuntimeError("Browser not initialized. Call init_browser() first.")

    try:
        _page.goto(url, timeout=17500)  # Increased from 15000 → 20000
        _page.wait_for_selector("body", timeout=12500)  # Increased from 10000 → 15000

        _page.mouse.move(100, 100)
        _page.keyboard.press("ArrowDown")

        # Increased wait buffer to give JS more time to render
        _page.wait_for_timeout(3000)  # Increased from 1000 → 3000

        text = BeautifulSoup(_page.content(), 'html.parser').get_text()

        if "has not been received" in text:
            add_invalid_url(url)
            return None
        return text

    except Exception as e:
        print(f"Error fetching dynamic content from {url}: {e}")
        add_invalid_url(url)
        return None


def getPdfText(pdf_url):
    """Extracts text from a PDF file."""
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        with open("temp.pdf", "wb") as temp_pdf:
            temp_pdf.write(response.content)
        text = ''
        with pdfplumber.open("temp.pdf") as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ''
        return text.strip()
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
