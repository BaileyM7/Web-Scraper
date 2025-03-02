from url_processing import getUrls, getStaticUrlText, getDynamicUrlText, arr, invalidArr
from openai_api import getKey, callApiWithText, OpenAI
import csv

processedResults = []  # List to store results

def callUrlApi():
    """Processes URLs, extracts content, and generates headlines via OpenAI."""
    client = OpenAI(api_key=getKey())
    for url in arr:
        if 'congress.gov' in url and not url.endswith('/text'):
            url += '/text'
        content = getDynamicUrlText(url) if 'congress.gov' in url else getStaticUrlText(url)
        if content:
            filename, headline, press_release = callApiWithText(content, client, url)
            if headline and press_release:
                press_release += f"\n* * # * * \n\nPrimary source of information: {url}"
                processedResults.append((url, filename, headline, press_release))

def writeResultsToCsv():
    """Writes processed results to a CSV file."""
    with open('csv/output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['URL', 'Filename', 'Headline', 'Press Release'])
        for url, filename, headline, message in processedResults:
            writer.writerow([url, filename, headline, message])


def writeUnusedUrlsToCsv():
    """Overwrites csv/input.csv with the contents of invalidArr."""
    with open('csv/tester.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        for url in invalidArr:
            writer.writerow([url])

    

# Execute functions
if __name__ == "__main__":
    getUrls()
    callUrlApi()
    writeResultsToCsv()
    print(invalidArr)
    writeUnusedUrlsToCsv()
