import csv
import re
from datetime import datetime
from openai import OpenAI
import pdfplumber
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse


# Instantiate variables
arr = []  # Holds raw URLs
pdfs = []  # Holds PDFs only
unavailableTexts = []  # Stores URLs that will be checked again later
processedResults = []  # List that stores the URL, filename, headline, and press release


# Get the OpenAI API key
def getKey():
    try:
        with open("key.txt", "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")


# Sorts URLs into PDFs and non-PDFs
def getUrls():
    try:
        with open('ExampleSheet.csv', 'r') as urls:
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


# Get text from a static URL
def getStaticUrlText(url):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL content: {e}")
        return None


def getDynamicUrlText(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Change headless to False
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=60000)


            # Wait for verification page to clear (increase timeout if necessary)
            page.wait_for_load_state("networkidle", timeout=60000)


            # Mimic user interaction
            page.wait_for_timeout(5000)  # Wait for Cloudflare verification
            page.mouse.move(100, 100)  # Move mouse to simulate user
            page.mouse.wheel(0, 1000)  # Scroll down
            page.wait_for_timeout(3000)  # Additional wait to load content


            # Extract page content
            return BeautifulSoup(page.content(), 'html.parser').get_text()
        except Exception as e:
            print(f"Error fetching dynamic content: {e}")
            return None
        finally:
            browser.close()




# Extract text from a PDF
def getPdfText(pdf_url):
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


# Clean text from OpenAI API response
def clean_text(text):
    text = re.sub(r'\*\*', '', text)  # Remove markdown bold (**)
    text = re.sub(r'""', '"', text)  # Remove duplicate double quotes
    # text = text.replace("\n", " ")  # Remove newline characters
    text = text.strip()
    text = text.replace('\"', "")  # Remove ""
    text = text.replace('Headline:', "")
    text = text.replace('headline:', "")
    text = text.replace('Headline', "")
    text = text.replace('headline', "")
    return text


# Call OpenAI API with extracted text
def callApiWithText(text, client, url):
    today = datetime.today()
    today_date = today.strftime('%b ') + str(today.day)
    file_date = datetime.today().strftime('%y%m%#d')
   
    if 'congress.gov' in url:
        bill_number = urlparse(url).path.rstrip("/").split("/")[-2] if url.endswith("/text") else urlparse(url).path.rstrip("/").split("/")[-1]
        filename = f"$H billintroh-{file_date}-hr{bill_number}"

        prompt = f"""Write a 300-word news story about the introduction of this House bill by a member of Congress. 

        Follow these guidelines:
        - The headline should start with only the government representative's last name, followed by 'introduces [Bill Name and Number: {bill_number}]' and the title of the bill.
        - The first paragraph should summarize the key details and purpose of the bill.
        - The story should be structured in paragraph format with a clear and informative flow.
        - Do not include the bill's introduction date.
        - Do not include quotes.

        Input data:
        Representative [Representative] has introduced [Bill]. Summary of bill:\n""" + text

    elif url.endswith(".pdf"):
        filename = "NA"
        prompt = """Summarize the report by first checking for an executive summary. If it has one, use that. If not, look for a
                summary instead. If neither is available, use the introduction. Summarize that data and include which companies are involved
                with this report. Do not include quotes.""" + text
    else:
        filename = "NA"
        prompt = "Create a headline and a press release in paragraph format that summarizes the given information. Do not include quotes." + text
   
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        result = response.choices[0].message.content
        headline, press_release = result.split('\n', 1)
        # print(headline)
        headline = clean_text(headline)
        press_release = clean_text(press_release)
        press_release = f"WASHINGTON, {today_date}. -- {press_release}"
        return filename, headline, press_release
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "NA", "", ""


# Process URLs
def callUrlApi():
    client = OpenAI(api_key=getKey())
    for url in arr:
        if 'congress.gov' in url and not url.endswith('/text'):
            url += '/text'
        content = getDynamicUrlText(url) if 'congress.gov' in url else getStaticUrlText(url)
        if content:
            filename, headline, press_release = callApiWithText(content, client, url)
            # print(content)
            if headline and press_release:
                processedResults.append((url, filename, headline, press_release))


# Write results to CSV
def writeResultsToCsv():
    with open('finishedMessages.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['URL', 'Filename', 'Headline', 'Press Release'])
        for url, filename, headline, message in processedResults:
            writer.writerow([url, filename, headline, message])


# Run all functions
getUrls()
callUrlApi()
writeResultsToCsv()




# template should look like this for the bills: [representative] has introduced [bill]. Summary of bill
# example
# Rep. Griffith, H. Morgan [R-VA-9] has introduced H.R.27 - HALT Fentanyl Act.


"""
https://www.congress.gov/bill/118th-congress/house-bill/10564
https://www.congress.gov/bill/118th-congress/house-bill/10259
"""

