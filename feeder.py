import csv
from openai import OpenAI
import pdfplumber
import requests


# instatiating variables
arr = []
finishedMessages = []
pdfs = []

# gets the given api key
def getKey():

    #trying to grab the key
    try:
        file = open("key.txt", "r")
        key = file.readline()
        file.close()
        return key
    
    # handling errors
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")

# gets the urls to be queried
def getUrls():

    #tring to read the downloadewd urls
    try:
        urls =  open('ExampleSheet.csv', 'r')
        reader = csv.reader(urls)

        # parsing through each url and adding it to the corresponding list
        for row in reader:
                url = row[0].strip()

                if 'pdf' in url.lower():
                    pdfs.append(url)
                else:
                    arr.append(url)

        for url in urls:
            # print(url)
            if 'pdf' in url:
                pdfs.append(url)
            else:
                arr.append(url)

        # closing the file after use
        urls.close()

    #handling errors
    except FileNotFoundError:
        print("File not found!")
    except PermissionError:
        print("You don't have permission to access this file.")
    except IOError as e:
        print(f"An I/O error occurred: {e}")

# gets text content from a url
def getUrlText(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        return response.text
    
    # shows error is cannot access website
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL content: {e}")
        return None

# gets all the text from a PDF URL
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
    
    # shows error for downloading the pdf
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None
    
    # shows general other erros that could occur
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

# Calls the OpenAI API with extracted text
def callApiWithText(text, client):
    # generating a prompt with all the text to give to the llm model
    prompt = (
        'Create a headline and a press release in paragraph format that summarizes the given information. '
        'Refer to the headline as "Headline" and the press release as "Press Release". '
        'Make the press releases around 400 words in length. Use quotes from the article to support your response. '
        'Here is the information: '\
    ) + text

    # calls the  chat gpt model api
    # we can use various modies, I use chose to go with 4o mini
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    # throws exception if an error occurs
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None


# calls api for url contents
def callUrlApi():
    # establishing a client
    client = OpenAI(api_key=getKey())

    # for each url, get its text, then call it with to the api
    for url in arr:
        content = getUrlText(url)

        # doesnt run api call if error occured
        if content:
            result = callApiWithText(content, client)
            if result:
                finishedMessages.append(result)

# calls api for the opdf contents
def callPdfApi():
    # establishing a client
    client = OpenAI(api_key=getKey())

    # for each pdf, get its text, then call it with to the api
    for pdf_url in pdfs:
        content = getPdfText(pdf_url)

        # doesnt run api call if error occured
        if content:
            result = callApiWithText(content, client)
            if result:
                finishedMessages.append(result)

# prints results to console to show user
def printResults():
    print("results:\n\n")

    for message in finishedMessages:
        print(message)

# calls all the functions
getUrls()
callUrlApi()
callPdfApi()
printResults()


'''
https://www.govexec.com/pay-benefits/2024/12/your-guide-pay-and-benefits-during-shutdown/401829/
https://www.govexec.com/technology/2024/12/tech-leader-says-doge-has-washington-inspired-and-fired/401763/?oref=ge-skybox-hp
https://federalnewsnetwork.com/government-shutdown/2023/10/on-the-brink-of-a-government-shutdown-the-senate-tries-to-approve-funding-but-its-almost-too-late/
https://www.dol.gov/ui/data.pdf
https://www.auditor.illinois.gov/Audit-Reports/Performance-Special-Multi/Performance-Audits/2024_Releases/24-DHS-ISC-Prgm-Ovrst-Perf-Full.pdf
'''


# https://www.congress.gov/bill/118th-congress/house-bill/10259/text

