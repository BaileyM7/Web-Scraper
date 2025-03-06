import csv
import requests
import pdfplumber
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

arr = []      # Holds raw URLs
pdfs = []     # Holds PDFs only
invalidArr = []

def getUrls(input_csv):
    """Loads URLs from the specified CSV file and sets flags accordingly."""
    global arr, pdfs, invalidArr

    try:
        with open(input_csv, 'r', encoding='utf-8') as urls:
            reader = csv.reader(urls)
            for row in reader:
                url = row[0].strip()
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
            invalidArr.append(url)
            return None
        else:
            return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL content: {e}")
        return None

def getDynamicUrlText(url):
    """Extracts text from a dynamically loaded web page using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=20000)
            page.wait_for_timeout(5000)
            page.mouse.move(100, 100)
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(3000)

            text = BeautifulSoup(page.content(), 'html.parser').get_text()

            if "has not been received" in text:
                invalidArr.append(url)
                return None
            else:
                return text
            
        except Exception as e:
            print(f"Error fetching dynamic content: {e}")
            url = url.replace("/text", "").replace("/cosponsors", "")
            invalidArr.append(url)
            return None
        finally:
            browser.close()

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
