import re
from datetime import datetime
from openai import OpenAI
from urllib.parse import urlparse
import platform

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
    """Cleans text for readability."""
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

def callApiWithText(text, cosponsorContent, client, url, is_senate):
    """
    Processes extracted text through OpenAI's API to generate headlines 
    and press releases, building either House or Senate style prompts and filenames.
    """
    today = datetime.today()

    # Decide how to handle month abbreviations (<=5 letters => spelled out, else abbreviate)
    month = today.strftime('%B') 
    short_month = today.strftime('%b')
    formatted_month = month if len(month) <= 5 else short_month + "."

    # Use '%d' for a zero-padded day
    day_format = '%-d' if platform.system() != 'Windows' else '%#d' # had to add this because i run the program on both mac and windows systems (very odd)

    today_date = f"{formatted_month} {today.strftime(day_format)}"
    file_date = get_date_from_text(text)

    # Extract final path component for the bill number
    # For a House link like: https://www.congress.gov/bill/119th-congress/house-bill/128/text
    # the second to last piece is "128"
    # For a Senate link like: https://www.congress.gov/bill/119th-congress/senate-bill/823/text
    bill_number = urlparse(url).path.rstrip("/").split("/")[-2] if url.endswith("/text") \
                  else urlparse(url).path.rstrip("/").split("/")[-1]
    
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
            - Starts with "Sen. [First Name] [Last Name], [Party]-[State],"
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
            - Starts with "Rep. [First Name] [Last Name], [Party]-[State],"
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
        headline = clean_text(headline)
        press_release = clean_text(press_release)
        press_release = f"\nWASHINGTON, {today_date} -- {press_release}\n"

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
        - Each cosponsor must follow this exact format:  
        `[Rep. Last Name, First Name] [Party-State-District]...[Date Cosponsored]`
        - The `...` (three dots) must always separate the district information from the date.
        - The output should be a single sentence listing all cosponsors separated by semicolons (`;`).

        Output Examples:
        Correct:
        'The bill ({cosponsor_bill_prefix}) introduced on [Introduction Date] has [Total Number] co-sponsors:  
        Rep. Smith, John [R-NY-5]...01/22/2025; Rep. Doe, Jane [D-CA-10]...01/24/2025.'

        Incorrect:
        - Missing `...` separator (`Rep. Smith, John [R-NY-5] 01/22/2025`)

        If there are no cosponsors, format the output exactly as:
        'The bill ({cosponsor_bill_prefix}) was introduced on [Introduction Date].'

        Ensure the format is **exact**, with no extra information or missing components.

        Cosponsor data:
        """ + cosponsorContent


        cosponsor_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": cosponsor_prompt}],
            max_tokens=5000
        )
        cosponsor_summary = clean_text(cosponsor_response.choices[0].message.content).strip("'")

        # Append cosponsor summary to the press release
        press_release += f"\n{cosponsor_summary}\n"

        return filename, headline, press_release
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "NA", "", ""


"""
senate has $H
filename needs the 6 digit date
get rid of #d for both house and senate
"""