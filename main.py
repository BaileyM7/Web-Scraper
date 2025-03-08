import sys
from url_processing import getUrls, getStaticUrlText, getDynamicUrlText, arr, invalidArr
from openai_api import getKey, callApiWithText, OpenAI
import csv

processedResults = []  # List to store results

# Determine House or Senate from command-line arguments
if len(sys.argv) < 2 or sys.argv[1] not in ['h', 's']:
    print("Usage: python main.py h | s")
    sys.exit(1)

is_senate = sys.argv[1] == 's'
input_csv = "csv/senate.csv" if is_senate else "csv/house.csv"

def callUrlApi():
    """Processes URLs, extracts content, and generates headlines via OpenAI."""
    client = OpenAI(api_key=getKey())

    for url in arr:
        if 'congress.gov' in url and not url.endswith('/text'):
            url += '/text'
        content = getDynamicUrlText(url) if 'congress.gov' in url else getStaticUrlText(url)
        cosponsorUrl = url.replace("/text", "/cosponsors")
        cosponsorContent = getDynamicUrlText(cosponsorUrl) if 'congress.gov' in cosponsorUrl else getStaticUrlText(cosponsorUrl)

        if content:
            filename, headline, press_release = callApiWithText(
                text=content,
                cosponsorContent=cosponsorContent,
                client=client,
                url=url,
                is_senate=is_senate
            )
            if headline and press_release:
                press_release += f"\n* * # * * \n\nPrimary source of information: {url}"
                processedResults.append((url, filename, headline, press_release))

def writeResultsToCsv():
    """Writes processed results to a CSV file."""
    with open('csv/output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['URL', 'Filename', 'Headline', 'Story'])
        for url, filename, headline, message in processedResults:
            writer.writerow([url, filename, headline, message])

def writeUnusedUrlsToCsv():
    """Overwrites the same input CSV (house or senate) with the contents of invalidArr."""
    with open(input_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for url in invalidArr:
            writer.writerow([url])

if __name__ == "__main__":
    # Pass is_senate and input_csv to getUrls dynamically
    getUrls(input_csv)

    callUrlApi()
    writeResultsToCsv()

    # Print invalid links for debugging
    print(invalidArr)
    writeUnusedUrlsToCsv()


"""
process of events:
1) run python3 scripts/populateCsv.py
2) For house: run % python3 main.py h 
2) For senate: run % python3 main.py s

Estimated Run Time: 30 seconds per url processed (only processed if it has text)
"""
