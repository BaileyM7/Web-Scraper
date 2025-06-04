#!/usr/bin/python3
import sys
import getopt
import csv
import logging
import time
from datetime import datetime

from url_processing import getUrls, getDynamicUrlText, arr, invalidArr
from openai_api import getKey, callApiWithText, OpenAI
from db_insert import get_db_connection
from scripts.populateCsv import populateCsv
from email_utils import send_summary_email
import openai_api

# --- Logging Setup ---
logfile = f"scrape_log.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M:%S",
    filename=logfile,
    filemode="w"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

# --- Insert Story Function ---
def insert_story(filename, headline, body, a_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicate filename
        check_sql = "SELECT COUNT(*) FROM story WHERE filename = %s"
        cursor.execute(check_sql, (filename,))
        if cursor.fetchone()[0] > 0:
            logging.info(f"Duplicate filename, skipping: {filename}")
            return False

        # Insert into story
        insert_sql = """
        INSERT INTO story
        (filename, uname, source, by_line, headline, story_txt, editor, invoice_tag,
         date_sent, sent_to, wire_to, nexis_sent, factiva_sent,
         status, content_date, last_action)
        VALUES (%s, %s, %s, %s, %s, %s, '', '', NOW(), '', '', NULL, NULL, %s, %s, SYSDATE())
        """
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(insert_sql, (
            filename,
            "T55-Bailey-Proj",
            a_id,
            "Bailey Malota",
            headline,
            body,
            'D',
            today_str
        ))

        # Get story ID s_id
        s_id = cursor.lastrowid

        # Insert state tags into story_tag
        tag_insert_sql = "INSERT INTO story_tag (id, tag_id) VALUES (%s, %s)"
        for state_abbr, tag_id in openai_api.found_ids.items():
            cursor.execute(tag_insert_sql, (s_id, tag_id))
            logging.debug(f"Inserted tag for state {state_abbr} (tag_id={tag_id})")

        conn.commit()
        logging.info(f"Inserted story and {len(openai_api.found_ids)} tag(s): {filename}")
        return True
    except Exception as err:
        logging.error(f"DB insert failed: {err}")
        return False
    finally:
        if conn:
            conn.close()


# --- Load Sources SQL Dump ---
def load_sources_sql(filepath="sources.dmp.sql"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        with open(filepath, 'r', encoding='utf-8') as f:
            statement = ""
            for line in f:
                if line.strip().startswith("--") or line.strip() == '':
                    continue
                statement += line
                if line.strip().endswith(";"):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logging.warning(f"Skipped SQL chunk due to error: {e}\n{statement.strip()}")
                    statement = ""
        conn.commit()
        logging.info("Loaded sources.dmp.sql successfully")
    except Exception as e:
        logging.error(f"Failed to load SQL file: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

# --- Main Processing ---
def main(argv):
    start_time = datetime.now()
    processed, skipped, total_urls = 0, 0, 0
    populate_first = False
    is_senate = None
    a_id = 0

    try:
        opts, args = getopt.getopt(argv, "Psh")
    except getopt.GetoptError:
        print("Usage: -P -s/-h")
        sys.exit(1)

    for opt, _ in opts:
        if opt == "-P":
            populate_first = True
        elif opt == "-s":
            is_senate = True
            a_id = 56
        elif opt == "-h":
            is_senate = False
            a_id = 57

    if is_senate is None:
        print("Must specify -s or -h")
        sys.exit(1)

    if populate_first:
        populateCsv()

    input_csv = "csv/senate.csv" if is_senate else "csv/house.csv"
    getUrls(input_csv)

    client = OpenAI(api_key=getKey())
    seen = set()

    for url in arr:
        canonical = url.strip().rstrip('/')
        if canonical in seen:
            continue
        seen.add(canonical)
        total_urls += 1

        if 'congress.gov' in url and not url.endswith('/text'):
            url += '/text'

        content = getDynamicUrlText(url, is_senate)
        if not content:
            continue

        filename_preview, _, _ = callApiWithText(
            text=content,
            client=client,
            url=url,
            is_senate=is_senate,
            filename_only=True  
        )

        if not filename_preview:
            logging.warning(f"Filename preview failed for {url}")
            skipped += 1
            continue

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM story WHERE filename = %s", (filename_preview,))
        if cursor.fetchone()[0] > 0:
            logging.info(f"Skipping duplicate before GPT call: {filename_preview}")
            skipped += 1
            conn.close()
            continue
        conn.close()

        filename, headline, press_release = callApiWithText(
            text=content,
            client=client,
            url=url,
            is_senate=is_senate, 
            filename_only=False
        )

        if filename == "NA" or not headline or not press_release:
            logging.warning(f"Skipped due to text not being available through api {url}")
            skipped += 1
            continue

        if filename and headline and press_release:
            full_text = press_release + f"\n\n* * # * *\nPrimary source of information: {url}"
            success = insert_story(filename, headline, full_text, a_id)
            if success:
                processed += 1
            else:
                skipped += 1


    end_time = datetime.now()
    elapsed = str(end_time - start_time).split('.')[0]
    summary = f"""
Load Version 2.0.1 06/03/2025
Docs Loaded: {processed}
URLS processed: {total_urls}
DUPS skipped: {skipped}
No Ledes found: 0

Passed Parameters:
Pull House and Senate: {'Senate' if is_senate else 'House'}
Number of days back: 1
Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Elapsed Time: {elapsed}
Character Minimum Amount: 100
"""
    logging.info(summary)
    send_summary_email(summary)

if __name__ == "__main__":
    main(sys.argv[1:])
