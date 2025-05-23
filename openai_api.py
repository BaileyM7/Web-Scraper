import re
from datetime import datetime
from openai import OpenAI
from urllib.parse import urlparse
import platform
from cleanup_text import cleanup_text

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

def clean_text(text):
    """Cleans text for readability and ASCII compliance."""
    text = cleanup_text(text)  # Replace non-ASCII chars
    text = re.sub(r'\*\*', '', text)  
    text = re.sub(r'""', '"', text)
    text = re.sub(r'###', '', text)
    text = text.strip().replace('\"', "").replace('Headline:', "").replace('headline:', "")
    return text

def get_date_from_text(text):
    pattern = r"Introduced in (?:Senate|House) \((\d{2})/(\d{2})/(\d{4})\)"
    
    match = re.search(pattern, text)
    if match:
        mm, dd, yyyy = match.groups()
        return f"{yyyy[-2:]}{mm}{dd}"
    return None

def get_date_from_cosponsor_summary(text):
    match = re.search(r'introduced on (\d{2})/(\d{2})/(\d{4})', text)
    if match:
        mm, dd, yyyy = match.groups()
        return f"{yyyy[-2:]}{mm}{dd}"
    return None

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

def callApiWithText(text, cosponsorContent, client, url, is_senate, filename_only=False):

    """
    Processes extracted text through OpenAI's API to generate headlines 
    and press releases, building either House or Senate style prompts and filenames.
    """

    
    # print(found_ids)

    today = datetime.today()

    text = re.sub(r'https://www\.congress\.gov[^\s]*', '', text)

    # Decide how to handle month abbreviations (<=5 letters => spelled out, else abbreviate)
    month = today.strftime('%B') 
    short_month = today.strftime('%b')
    formatted_month = month if len(month) <= 5 else short_month + "."

    # Use '%d' for a zero-padded day
    day_format = '%-d' if platform.system() != 'Windows' else '%#d' # had to add this because i run the program on both mac and windows systems (very odd)

    today_date = f"{formatted_month} {today.strftime(day_format)}"
    file_date = get_date_from_text(text)



    # if file_date:
    #     filename = f"$H billintros-{file_date}-s{bill_number}" if is_senate \
    #         else f"$H billintroh-{file_date}-hr{bill_number}"
    
    # Extract final path component for the bill number
    # For a House link like: https://www.congress.gov/bill/119th-congress/house-bill/128/text
    # the second to last piece is "128"
    # For a Senate link like: https://www.congress.gov/bill/119th-congress/senate-bill/823/text
    bill_number = urlparse(url).path.rstrip("/").split("/")[-2] if url.endswith("/text") \
                  else urlparse(url).path.rstrip("/").split("/")[-1]
    
    if is_senate:
        filename = f"$H billintros-{file_date}-s{bill_number}"
    else:
        filename = f"$H billintroh-{file_date}-hr{bill_number}"

    if filename_only:
        return filename, None, None
    
    if 'congress.gov' in url:
        # Different filename & prompt depending on House or Senate
        if is_senate:
            # Senate
            filename = f"$H billintros-{file_date}-s{bill_number}"
            prompt = f"""
            Write a 300-word news story about this Senate bill, following these exact formatting rules:
            
            Headline:
            - Starts with "Sen. [Last Name] Introduces [Bill Name]" 
            (Do not include the bill number in the headline.)

            First Paragraph
            - Starts with "Sen. [First Name] [Last Name], [Party]-[State Postal Codes],"
            - Clearly summarize the key details and purpose of the bill.

            Body Structure
            - Use structured paragraphs with an informative flow
            - Do not include quotes.
            - Provide context such as:
              * Why the bill was introduced.
              * Its potential impact.
              * Relevant background details.

            Bill Details  
            Senator [Senator] has introduced [Bill Name]. 
            Summary of the bill:

            """ + text
        else:
            # House
            filename = f"$H billintroh-{file_date}-hr{bill_number}"
            prompt = f"""
            Write a 300-word news story about this House bill, following these exact formatting rules:

            Headline:
            - Starts with "Rep. [Last Name] Introduces [Bill Name]"
            (Do not include the bill number in the headline.)

            First Paragraph
            - Starts with "Rep. [First Name] [Last Name], [Party]-[State Postal Codes],"
            - Clearly summarize the key details and purpose of the bill.

            Body Structure
            - Use structured paragraphs with an informative flow
            - Do not include quotes.
            - Provide context such as:
              * Why the bill was introduced.
              * Its potential impact.
              * Relevant background details.

            Bill Details
            Representative [Representative] has introduced [Bill Name].
            Summary of the bill:

            """ + text

    elif url.endswith(".pdf"):
        filename = "NA"
        prompt = (
            "Summarize this report, prioritizing an executive summary. "
            "If unavailable, summarize the introduction. " + text
        )
    else:
        filename = "NA"
        prompt = (
            "Create a headline and press release summarizing the given information. "
            "Do not include quotes." + text
        )

    # Call the model
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens= 2500
        )
        result = response.choices[0].message.content
        # Attempt to split the result so that the first line is the headline
        # and everything else is the press release
        headline, press_release = result.split('\n', 1)
        headline = clean_text(headline).strip()
        press_release = clean_text(press_release)
        press_release = f"WASHINGTON, {today_date} -- {press_release}\n"

        # Second API call for cosponsor summary
        # Notice the difference in the name (H.R. vs S.) is not strictly coded here,
        # but you could adapt. Below uses "H.R. {bill_number}" by default if is_senate=False.
        # Or you might parse more carefully and do "S. {bill_number}" if is_senate=True.
        if is_senate:
            cosponsor_bill_prefix = f"S. {bill_number}"
        else:
            cosponsor_bill_prefix = f"H.R. {bill_number}"

        cosponsor_prompt = f"""
        Extract and summarize the cosponsors of the bill identified by its number (e.g., {cosponsor_bill_prefix}) 
        and introduction date.

        Strict Formatting Requirements:
        - Always use **numerals** (e.g., "0", "1", "23", "101") to indicate the number of cosponsors — never write out the word form (e.g., "one", "twenty").
        - If there are **fewer than 101** cosponsors, list each one in this exact format:
        `[Rep. Last Name, First Name] [Party-State-District]...[Date Cosponsored]`
        - The `...` (three dots) must always separate the district information from the date.
        - The output must be a single sentence listing all cosponsors separated by semicolons (`;`).

        - If there are **101 or more** cosponsors, return this exact sentence:
        'The bill ({cosponsor_bill_prefix}) introduced on [Introduction Date] has [Total Number] co-sponsors.'

        Examples:
         **Correct when <101 cosponsors:**  
        'The bill ({cosponsor_bill_prefix}) introduced on [Introduction Date] has [Total Number] co-sponsors:  
        Rep. Smith, John [R-NY-5]...01/22/2025; Rep. Doe, Jane [D-CA-10]...01/24/2025.'

         **Correct when ≥101 cosponsors:**  
        'The bill ({cosponsor_bill_prefix}) introduced on [Introduction Date] has [Total Number] co-sponsors.'

        - If there are **no cosponsors**, format the output exactly as:
        'The bill ({cosponsor_bill_prefix}) was introduced on [Introduction Date].'

        Ensure the format is exact, with no extra information or missing components.

        Cosponsor data:
        """ + cosponsorContent

        cosponsor_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": cosponsor_prompt}],
            max_tokens=5000
        )
        cosponsor_summary = re.sub(r'\s+', ' ', cosponsor_response.choices[0].message.content).strip("'")

        if not file_date:
            file_date = get_date_from_cosponsor_summary(cosponsor_summary)
        if is_senate:
            filename = f"$H billintros-{file_date}-s{bill_number}"
        else:
            filename = f"$H billintroh-{file_date}-hr{bill_number}"
            
        # Append cosponsor summary to the press release
        press_release += f"\n{cosponsor_summary}\n"

        # print("==== DEBUG: Press release text before state extraction ====")
        # print(press_release)

        extract_found_ids(press_release)

        return filename, headline, press_release
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "NA", "", ""
