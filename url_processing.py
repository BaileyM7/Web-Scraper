import re
import csv
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

arr = []
invalidArr = []


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

# now uses api to get it instead of webscraping
def getDynamicUrlText(url, is_senate):
    """Fetch bill text using Congress.gov API and fallback to govinfo.gov."""
    with open("utils/govkey.txt") as f:
        api_key = f.read().strip()

    congress = 119

    match = re.search(r'/bill/(\d+)[a-z\-]*/(senate|house)-bill/(\d+)', url)
    if not match:
        # print(f"Unable to parse bill info from URL: {url}")
        add_invalid_url(url)
        return None

    _, bill_type_text, bill_number = match.groups()
    bill_type = "s" if is_senate else "hr"

    api_url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}/text"
    # print(api_url)
    headers = {"X-API-Key": api_key}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # raises HTTPError for 4xx or 5xx
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch bill text for {url}: {e}")
        add_invalid_url(url)
        return None

    if response.status_code == 200:
        data = response.json()
        versions = data.get("billText", {}).get("versions", [])
        for version in versions:
            for fmt in version.get("formats", []):
                if fmt["format"] == "html":
                    html_url = fmt["url"]
                    html_response = requests.get(html_url)
                    if html_response.status_code == 200:
                        text = html_response.text.replace("<html><body><pre>", "").strip()
                        return text
        #             else:
        #                 print(f"Failed to fetch HTML content: {html_response.status_code}")
        # print("HTML version not found in formats.")
    # else:
    #     print(f"Congress API failed: {response.status_code}")

    # Fallback: govinfo.gov
    #print("Trying govinfo.gov...")
    if is_senate:
        govinfo_url = f"https://www.govinfo.gov/content/pkg/BILLS-{congress}{bill_type}{bill_number}is/html/BILLS-{congress}{bill_type}{bill_number}is.htm"
    else:

        govinfo_url = f"https://www.govinfo.gov/content/pkg/BILLS-{congress}{bill_type}{bill_number}ih/html/BILLS-{congress}{bill_type}{bill_number}ih.htm"
        
    response = requests.get(govinfo_url)
    if response.status_code == 200:
        # print(f"Found bill text on govinfo.gov: {govinfo_url}")
        return response.text
    else:
        # print("Bill text not yet published on govinfo.gov.")
        add_invalid_url(url)
        return None

def get_primary_sponsor(is_senate, num, bill_number):
    """
    Returns the full sponsor name string as it appears in Congress.gov API (e.g., 'Sen. Sheehy, Tim [R-MT]')
    """
    with open("utils/govkey.txt") as f:
        api_key = f.read().strip()
    
    if is_senate:
        congress = "s"
    else:
        congress = "hr"
    
    url = f"https://api.congress.gov/v3/bill/{num}/{congress}/{bill_number}?api_key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        sponsors = data.get("bill", {}).get("sponsors", [])
        if not sponsors:
            print("No sponsor data found.")
            return None

        primary = sponsors[0]
        # print(primary.get("fullName", None))
        # print(primary.get("fullName", None))
        match = re.match(r"^(?:Rep\.|Sen\.|Del\.)\s+([A-Za-z\-'\s]+?),", primary.get("fullName", None))
        # last_name = primary.get("fullName", None).split(',')[0]
        # print(left_of_comma)
        last_name = match.group(1)
        # print(last_name)
        full_name = primary.get("fullName", None).split('.', 1)[1].strip()
        full_name = re.sub(r"\[(\w+)-(\w+)-\d+\]", r"[\1-\2]", full_name)
        full_name = full_name.replace("-At Large", "")
        # print(full_name)
        return full_name, last_name

    except requests.exceptions.RequestException as e:
        print(f"No info found: {e}")
        return None



