import csv
from openai import OpenAI
import pdfplumber
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# instantiate variables
arr = [] # holds raws urls
pdfs = [] # holds pdfs only
unavailableTexts = []  # stores urls that will be checked again later
processedResults = []  # list that stores the url, message pair

# gets the OpenAi Key
def getKey():
    try:
        with open("key.txt", "r") as file:
            key = file.readline().strip()
            return key

    # error handling if the file cannot be opened
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")

# sorts the given urls into pdfs and non-pdfs
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

    # handles erros with not being able to open file
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")


# if static url, gather content
def getStaticUrlText(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    # gets the text from the website
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL content: {e}")
        return None

# gets text content from  dynamic url using Playwright
def getDynamicUrlText(url):

    # this is done to circumvent bot detection
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # use headful mode to better mimic real users (gets around anit-bot stuff)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
        )
        
        page = context.new_page()


        try:
            # got to the URL
            page.goto(url, timeout=60000)

            # waits for JavaScript to load specific elements (adjust selector as needed)
            page.wait_for_selector("body", timeout=30000)

            # handles potential cloudflare checks or intermediate screens
            if "checking your browser" in page.content():
                print("Cloudflare challenge detected, waiting for resolution...")
                page.wait_for_load_state("networkidle")

            # get rendered content
            content = page.content()  # gets html
            soup = BeautifulSoup(content, 'html.parser')

            # checks to see if the bill text is available
            if "text has not been received" in soup.get_text():
                print(f"Bill text not available for URL: {url}")
                unavailableTexts.append(url)
                return None

            return soup.get_text()

        # error handling
        except Exception as e:
            print(f"Error fetching dynamic content: {e}")
            return None

        # closes browser
        finally:
            browser.close()

# scraped pdfs using pdfplumber
def getPdfText(pdf_url):
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        with open("temp.pdf", "wb") as temp_pdf:
            temp_pdf.write(response.content)

        text = ''
        with pdfplumber.open("temp.pdf") as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text
    
    # error handling if pdfplumber runs into issues
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

# calls OpenAI API with extracted text
def callApiWithText(text, client):

    # this should generate the headline and press release
    prompt = (
        'Create a headline and a press release in paragraph format that summarizes the given information. '
        'Refer to the headline as "Headline" and the press release as "Press Release". '
        'Make the press releases around 400 words in length. Use quotes from the article to support your response. '
        'Here is the information: ' + text
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

# processes all urls 
def callUrlApi():
    client = OpenAI(api_key=getKey())

    for url in arr:
        if 'congress.gov' in url:
            content = getDynamicUrlText(url+ "/text/ih?format=txt")
        else:
            content = getStaticUrlText(url)

        if content:
            result = callApiWithText(content, client)
            if result:
                processedResults.append((url, result))

# processes all pdfs
def callPdfApi():
    client = OpenAI(api_key=getKey())

    for pdf_url in pdfs:
        content = getPdfText(pdf_url)
        if content:
            result = callApiWithText(content, client)
            if result:
                processedResults.append((pdf_url, result))

# sends results to finishedMessages.csv
def writeResultsToCsv():
    with open('finishedMessages.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['URL', 'Message'])  # Write header
        for url, message in processedResults:
            writer.writerow([url, message])

# sends unavailable URLs to unavailable.csv (to be ran again later)
def writeUnavailableToCsv():
    with open('unavailable.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL'])  # Write header
        for url in unavailableTexts:
            writer.writerow([url])
 
# runs all the functions
getUrls()
callUrlApi()
callPdfApi()
writeResultsToCsv()
writeUnavailableToCsv()
