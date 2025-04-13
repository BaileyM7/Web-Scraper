import sys
from url_processing import getUrls, getStaticUrlText, getDynamicUrlText, arr, invalidArr
from openai_api import getKey, callApiWithText, OpenAI
from db_insert import insert_press_release
from datetime import datetime
import logging

processedResults = []

# Determine House or Senate
if len(sys.argv) < 2 or sys.argv[1] not in ['h', 's']:
    print("Usage: python main.py h | s")
    sys.exit(1)

is_senate = sys.argv[1] == 's'
input_csv = "csv/senate.csv" if is_senate else "csv/house.csv"
a_id = 40433 if is_senate else 40434

def callUrlApi():
    """Processes URLs, extracts content, and generates headlines via OpenAI."""
    client = OpenAI(api_key=getKey())

    for url in arr:
        if 'congress.gov' in url and not url.endswith('/text'):
            url += '/text'

        content = getDynamicUrlText(url) if 'congress.gov' in url else getStaticUrlText(url)

        if content:
            cosponsorUrl = url.replace("/text", "/cosponsors")
            cosponsorContent = getDynamicUrlText(cosponsorUrl) if 'congress.gov' in cosponsorUrl else getStaticUrlText(cosponsorUrl)

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

def writeInvalidUrls():
    """Overwrites the same input CSV (house or senate) with the invalid URLs."""
    import csv
    with open(input_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for url in invalidArr:
            writer.writerow([url])

if __name__ == "__main__":
    getUrls(input_csv)

    callUrlApi()

    # Insert into database
    today_str = datetime.today().strftime("%Y-%m-%d")
    for url, filename, headline, message in processedResults:
        insert_press_release(headline, today_str, message, a_id, filename)

    # Print or log invalids
    print("Invalid URLs:", invalidArr)
    writeInvalidUrls()


"""
process of events:
1) run python3 scripts/populateCsv.py
2) For house: run %  caffeinate -d python3 main.py h 
2) For senate: run % caffeinate -d python3 main.py s 


Run this to check db

SELECT filename, a_id, headline, body_txt
FROM tns.press_release
ORDER BY create_date DESC
LIMIT 5;



Estimated Run Time: 30 seconds per url processed (only processed if it has text)
"""

"""
TODO
* bug where filename gives: $H billintros-None-s5 (for senate number 5) 
* implement the kevin sql stuffs

"""