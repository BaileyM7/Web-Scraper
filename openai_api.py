import re
from datetime import datetime
from openai import OpenAI
from urllib.parse import urlparse
import platform
from cleanup_text import cleanup_text
from url_processing import add_invalid_url, get_primary_sponsor
import subprocess
import ast
import requests

global found_ids
found_ids = {}

# used for tagging purposes
state_ids = {
 'AL' :67,                          
 'AK' :68,                          
 'AZ' :69,                          
 'AR' :70,                          
 'CA' :71,                          
 'CO' :72,                          
 'CT' :73,                          
 'DE' :74,                          
 'DC' :75,                          
 'FL' :76,                          
 'GA' :77,                          
 'HI' :78,                          
 'ID' :79,                          
 'IL' :80,                          
 'IN' :81,                          
 'IA' :82,                          
 'KS' :83,                          
 'KY' :84,                          
 'LA' :85,                          
 'ME' :86,                          
 'MD' :87,                          
 'MA' :88,                          
 'MI' :89,                          
 'MN' :90,                          
 'MS' :91,                          
 'MO' :92,                          
 'MT' :93,                          
 'NE' :94,                          
 'NV' :95,                          
 'NH' :96,                          
 'NJ' :97,                          
 'NM' :98,                          
 'NY' :99,                          
 'NC' :100,                         
 'ND' :101,                         
 'OH' :102,                         
 'OK' :103,                         
 'OR' :104,                         
 'PA' :105,                         
 'RI' :106,                         
 'SC' :107,                         
 'SD' :108,                         
 'TN' :109,                         
 'TX' :110,                         
 'UT' :111,                         
 'VT' :112,                         
 'VA' :113,                         
 'WA' :114,                         
 'WV' :115,                         
 'WI' :116,                         
 'WY' :117,                         
}

# gets the api keys
def getKey():
    """Retrieves the OpenAI API key from a file."""
    try:
        with open("utils/key.txt", "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")

# Cleans text for readability and ASCII compliance.
def clean_text(text):
    text = cleanup_text(text)  # Replace non-ASCII chars
    text = re.sub(r'\*\*', '', text)  
    text = re.sub(r'""', '"', text)
    text = re.sub(r'###', '', text)
    text = text.strip().replace('\"', "").replace('Headline:', "").replace('headline:', "")
    return text

def get_date_from_text(text, is_file):
    """
    Extract the introduction date after:
    'IN THE HOUSE OF REPRESENTATIVES' or 'IN THE SENATE OF THE UNITED STATES',
    allowing for extra text like "(legislative day, March 10)" between the date.
    
    If is_file is True, returns the date as MMDDYY (e.g., "031125").
    If is_file is False, returns the date as MM/DD/YYYY (e.g., "03/11/2025").
    """
    pattern = (
        r"IN THE (?:HOUSE OF REPRESENTATIVES|SENATE OF THE UNITED STATES)[^\n]*\n"
        r"\s*([A-Z][a-z]+ \d{1,2})(?: \([^)]+\))?, (\d{4})"
    )
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        try:
            full_date = f"{match.group(1)}, {match.group(2)}"  # e.g., "March 11, 2025"
            dt = datetime.strptime(full_date, "%B %d, %Y")
            if is_file:
                # Return as YYMMDD with leading zeros
                return dt.strftime("%y%m%d")
            else:
                # Return as MM/DD/YYYY
                return dt.strftime("%m/%d/%Y")
        except ValueError:
            return None
    return None

# def get_date_from_cosponsor_summary(text):
#     match = re.search(r'introduced on (\d{2})/(\d{2})/(\d{4})', text)
#     if match:
#         mm, dd, yyyy = match.groups()
#         return f"{yyyy[-2:]}{mm}{dd}"
#     return None

def extract_found_ids(press_release):
    global found_ids
    found_ids = {}

    # Match either [R-UT], [D-NY-14], or R-UT, D-TX (non-bracketed)
    pattern = re.compile(r'\b[DRI]-([A-Z]{2})(?:-\d{1,2})?\b')


    matches = pattern.findall(cleanup_text(press_release))

    for abbr in set(matches):
        if abbr in state_ids:
            found_ids[abbr] = state_ids[abbr]
    # print(found_ids)
    # print(len(found_ids))
    return found_ids

def callApiWithText(text, client, url, is_senate, filename_only=False):
    # gathering info to then create the output for filename, headline, and body
    today = datetime.today()
    text = re.sub(r'https://www\.congress\.gov[^\s]*', '', text)
    month = today.strftime('%B') 
    short_month = today.strftime('%b')
    formatted_month = month if len(month) <= 5 else short_month + "."
    day_format = '%-d' if platform.system() != 'Windows' else '%#d'
    today_date = f"{formatted_month} {today.strftime(day_format)}"
    bill_number = urlparse(url).path.rstrip("/").split("/")[-2] if url.endswith("/text") else urlparse(url).path.rstrip("/").split("/")[-1]

    file_date = get_date_from_text(text, True)

    if file_date is None:
        add_invalid_url(url)
        return "NA", None, None
    
    filename = f"$H billintros-{file_date}-s{bill_number}" if is_senate else f"$H billintroh-{file_date}-hr{bill_number}"

    if filename_only:
        return filename, None, None
    
    primary_sponsor, last_name = get_primary_sponsor(is_senate, 119, bill_number)

    prompt = f"""
    Write a 300-word news story about this {'Senate' if is_senate else 'House'} bill, following these rules:

    Headline:
    - Starts with {'Sen.' if is_senate else 'Rep.'} {last_name} [Last Name] Introduces [Bill Name]
    (Do not include the bill number in the headline.)

    First Paragraph:
    - Start the first line with: {'Sen.' if is_senate else 'Rep.'} [First Name] [Last Name], [Party Initial]-[State Abbreviation], e.g., Rep. Julia Letlow, R-LA,
    - Do not use parentheses around the party and state.
    - There must be a comma both before and after the party-state block — like: Sen. Tim Scott, R-SC,
    - Summarize the bill’s purpose.


    Body:
    - Use structured paragraphs.
    - No quotes.
    - Add context (motivation, impact, background).
    - Do not mention or list any cosponsors or other legislators by name.
    - Focus only on the primary sponsor and the bill content.

    Bill Details:
    {'Sen.' if is_senate else 'Rep.'} [Last Name] has introduced [Bill Name]. 
    Summary of the bill:
    {text}
    Primary Sponsor's Name and State Code: 
    {primary_sponsor}
    """

    try:
        # Generate main press release
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500
        )
        result = response.choices[0].message.content
        headline, press_body = result.split('\n', 1)
        headline = clean_text(headline)
        press_body = clean_text(press_body)
        press_release = f"WASHINGTON, {today_date} -- {press_body.strip()}"

        # Add cosponsor summary from CLI
        cosummary = generate_cosponsor_summary(url, text, is_senate, bill_number)
        press_release += f"\n\n{cosummary}"

        press_release = clean_text(press_release)
        extract_found_ids(press_release)

        return filename, headline, press_release

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "NA", "", ""

# gets the cosponsor summary (now without the use of the GPT api)
def generate_cosponsor_summary(url, text, is_senate, bill_num):

    intro_date = get_date_from_text(text, False)
    congress_num = 119

    # setting labels determined by is_senate
    title = "Sen. " if is_senate else "Rep. "
    label = "S. " if is_senate else "H.R. "
    url_label = "s" if is_senate else "hr"

    # creating the url to be used in the get request
    url = (
        f"https://api.congress.gov/v3/bill/{congress_num}/{url_label}/{bill_num}/cosponsors" if is_senate 
        else f"https://api.congress.gov/v3/bill/{congress_num}/{url_label}/{bill_num}/cosponsors"
    )

    # grabbing gov data api key
    api_key = ""
    with open("utils/govkey.txt", "r") as file:
                api_key =  file.readline().strip()
    parameters = {
        "api_key": api_key,
        "limit": 500
    }

    # getting the json response
    response = requests.get(url, parameters)
    cosponsors = response.json()['cosponsors']

    # print(cosponsors)
    num_cosponsors = len(cosponsors)

    # creating and formatting the total paragram
    cosponsors_str = f"The bill ({label}{bill_num}) introduced on {intro_date} has {num_cosponsors} co-sponsors: "
    count = 0
    if num_cosponsors == 0:
        cosponsors_str = f"The bill ({label}{bill_num}) was introduced on {intro_date}."
    for c in cosponsors:
        count += 1
        if count < num_cosponsors:
            cosponsors_str += f"{c.get('lastName', "")}, {c.get('firstName', "")} [{c.get('party', "")}-{c.get('state', "")}]...{c.get('sponsorshipDate', "")}; "
        else:
            cosponsors_str += f"{c.get('lastName', "")}, {c.get('firstName', "")} [{c.get('party', "")}-{c.get('state', "")}]...{c.get('sponsorshipDate', "")}."

    return cosponsors_str


