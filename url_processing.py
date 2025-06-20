import re
import csv
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from db_insert import get_db_connection
import html

arr = []
invalidArr = []


def load_pending_urls_from_db(is_senate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, url FROM url_queue
            WHERE status = 'pending' AND chamber = %s
            LIMIT 2000
        """, ('senate' if is_senate else 'house',))
        return cursor.fetchall()  # returns list of (id, url)
    finally:
        conn.close()

def mark_url_processed(url_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE url_queue SET status = 'processed' WHERE id = %s", (url_id,))
        conn.commit()
    finally:
        conn.close()

def mark_url_invalid(url_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE url_queue SET status = 'invalid' WHERE id = %s", (url_id,))
        conn.commit()
    finally:
        conn.close()


# now uses api to get it instead of webscraping
def getDynamicUrlText(url, is_senate):
    """Fetch bill text using Congress.gov API and fallback to govinfo.gov."""
    with open("utils/govkey.txt") as f:
        api_key = f.read().strip()

    congress = 119

    match = re.search(r'/bill/(\d+)[a-z\-]*/(senate|house)-bill/(\d+)', url)
    if not match:
        # print(f"Unable to parse bill info from URL: {url}")
        # add_invalid_url(url)
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
        # add_invalid_url(url)
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

        if "Page Not Found" in response.text or "Error occurred" in response.text:
            return None
        
        return response.text
    else:
        # print("Bill text not yet published on govinfo.gov.")
        # add_invalid_url(url)
        return None

def get_primary_sponsor(is_senate, congress_num, bill_number):
    """
    Returns the full sponsor name string as it appears in Congress.gov API (e.g., 'Sen. Sheehy, Tim [R-MT]')
    """
    with open("utils/govkey.txt") as f:
        api_key = f.read().strip()
    
    # title = "Sen. " if is_senate else "Rep. "
    # label = "S. " if is_senate else "H.R. "
    url_label = "s" if is_senate else "hr"

    url = f"https://api.congress.gov/v3/bill/{congress_num}/{url_label}/{bill_number}" 

    parameters = {
    "api_key": api_key,
    "limit": 250
    }
    
    try: 
        # first request
        response = requests.get(url, parameters)
        response.raise_for_status()
        sponsor = response.json()['bill']['sponsors']

        # second request
        name_url = sponsor[0]['url']
        directOrderID = requests.get(name_url, parameters)
        sponsor_name = directOrderID.json()['member']['directOrderName']
        last_name = directOrderID.json()['member']['lastName']

    except requests.exceptions.HTTPError as e:
        status = response.status_code
        if status == 502:
            print(f"502 Bad Gateway for URL: {url}")
            return "", ""
        elif status == 429:
            print(f"429 Too Many Requests for URL: {url}")
            return "STOP", ""
        else:
            print(f"HTTP error {status} for URL: {url}")
            return "", ""
    
    sponsor_str = ""

    if not sponsor:
        print(f"No sponsors found for {url}")
        return "", ""

    sponsor_str += f"{sponsor_name}, {sponsor[0]['party']}-{sponsor[0]['state']},"

    return sponsor_str, last_name


def extract_sponsor_phrase(html_string):
    decoded = html.unescape(html_string)

    # Extract <pre> ... </pre>
    pre_match = re.search(r"<pre>(.*?)</pre>", decoded, re.DOTALL)
    if not pre_match:
        return None
    pre_text = pre_match.group(1)

    # Match up to the word 'introduced' — no whitespace requirement
    match = re.search(
        r"((?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+.*?)(?=introduced)",
        pre_text,
        re.DOTALL
    )

    if match:
        return ' '.join(match.group(1).split())  # normalize whitespace
    return None

# method adds story id from inserted story into url queue
def link_story_to_url(url_id, s_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE url_queue SET story_id = %s WHERE id = %s", (s_id, url_id))
        conn.commit()
    finally:
        conn.close()

# adds note to url in url queue
def add_note_to_url(url_id, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE url_queue SET notes = %s WHERE id = %s", (message, url_id))
        conn.commit()
    finally:
        conn.close()