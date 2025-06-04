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
        cosummary = generate_cosponsor_summary(url, text)
        press_release += f"\n\n{cosummary.strip()}"

        press_release = clean_text(press_release)
        extract_found_ids(press_release)

        return filename, headline, press_release

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "NA", "", ""

# gets the cosponsor summary (now without the use of the GPT api)
def generate_cosponsor_summary(url, text):
    # print("TEXT:", text)
    intro_date = get_date_from_text(text, False)
    def parse_bill_url(url):
        match = re.search(r'/bill/(\d+)[a-z\-]*/(senate|house)-bill/(\d+)', url)
        if not match:
            raise ValueError(f"Invalid Congress.gov bill URL: {url}")
        congress, chamber, number = match.groups()
        bill_type = "s" if chamber == "senate" else "hr"
        bill_code = f"S. {number}" if chamber == "senate" else f"H.R. {number}"
        return int(congress), bill_type, int(number), bill_code

    def run_cli_command(endpoint):
        result = subprocess.run(
            ["python", "cdg_cli.py", endpoint],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("CLI call failed:\n", result.stderr)
            return None
        lines = result.stdout.splitlines()
        dict_start = next((i for i, line in enumerate(lines) if line.strip().startswith("{")), None)
        if dict_start is None:
            # print("No co-sponsors for given bill")
            return None
        raw_dict_str = "\n".join(lines[dict_start:])
        try:
            return ast.literal_eval(raw_dict_str)
        except Exception as e:
            print("Failed to parse CLI output:", e)
            return None

    # Parse URL into parts
    try:
        congress, bill_type, bill_number, bill_code = parse_bill_url(url)
    except ValueError as ve:
        return str(ve)

    # Build endpoint and fetch cosponsors
    endpoint = f"bill/{congress}/{bill_type}/{bill_number}/cosponsors"
    all_cosponsors = []
    while endpoint:
        data = run_cli_command(endpoint)
        if not data:
            break
        all_cosponsors.extend(data.get("cosponsors", []))
        endpoint = None
        if "next" in data.get("pagination", {}):
            next_url = data["pagination"]["next"]
            if "/v3/" in next_url:
                endpoint = next_url.split("/v3/")[-1]

    # formatting the outputs
    count = len(all_cosponsors)
    if not intro_date:
        intro_date = "____/____/________"

    # special output if their arent any cosponsors
    if count > 0:
        summary = f"\nThe bill ({bill_code}) introduced on {intro_date} has {count} co-sponsor"
        summary += "s: " if count != 1 else ": "

        entries = []
        for person in all_cosponsors:
            first = person.get("firstName", "")
            last = person.get("lastName", "")
            party = person.get("party", "")
            state = person.get("state", "")
            date = person.get("sponsorshipDate", "Unknown Date")

            first = first.capitalize()
            last  = last.capitalize()

            entries.append(f"{last}, {first} [{party}-{state}]...{date}")

        summary += " ".join(entries)
        summary += "."
    else:
        summary = f"\nThe bill ({bill_code}) was introduced on {intro_date}."
    return summary


