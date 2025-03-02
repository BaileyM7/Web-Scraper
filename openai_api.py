import re
from datetime import datetime
from openai import OpenAI
from urllib.parse import urlparse

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

def callApiWithText(text, client, url):
    """Processes extracted text through OpenAI's API to generate headlines and press releases."""
    today = datetime.today()
    today_date = today.strftime('%b. ') + str(today.day)
    file_date = datetime.today().strftime('%y%m%#d')

    if 'congress.gov' in url:
        bill_number = urlparse(url).path.rstrip("/").split("/")[-2] if url.endswith("/text") else urlparse(url).path.rstrip("/").split("/")[-1]
        filename = f"$H billintroh-{file_date}-hr{bill_number}"
        prompt = f"""Write a 300-word news story about this House bill, following these exact formatting rules:
            Headline:
            - Starts with "Rep. [Last Name] Introduces [Bill Name]" 
            (Do not include the bill number in the headline.)

             First Paragraph
            - Starts with Rep. [First Name] [Last Name], [Party]-[State],"
            - Example: Rep. John Smith, D-California,"
            - Clearly summarize the key details and purpose of the bill.

             Body Structure
            - Use structured paragraphs with an informative flow
            - Do not include quotes.
            - Provide context such as:
            - Why the bill was introduced.
            - Its potential impact.
            - Relevant background details.

            Bill Details  
            Representative [Representative] has introduced [Bill Name].  
            Summary of the bill:  
            """ + text

    elif url.endswith(".pdf"):
        filename = "NA"
        prompt = """Summarize this report, prioritizing an executive summary. If unavailable, summarize the introduction.""" + text
    else:
        filename = "NA"
        prompt = "Create a headline and press release summarizing the given information. Do not include quotes." + text

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        result = response.choices[0].message.content
        headline, press_release = result.split('\n', 1)
        headline = clean_text(headline)
        press_release = clean_text(press_release)
        press_release = f"\nWASHINGTON, {today_date} -- {press_release}\n"
        return filename, headline, press_release
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "NA", "", ""
