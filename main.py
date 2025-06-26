#!/usr/bin/python3
import sys
import getopt
import csv
import logging
import time
from datetime import datetime

from url_processing import getDynamicUrlText, load_pending_urls_from_db, mark_url_processed, extract_sponsor_phrase, link_story_to_url, add_note_to_url
from openai_api import getKey, callApiWithText, OpenAI
from db_insert import get_db_connection
from populateCsv import populateCsv
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
def insert_story(filename, headline, body, a_id, sponsor_blob):
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
         status, content_date, last_action, orig_txt)
        VALUES (%s, %s, %s, %s, %s, %s, '', '', NOW(), '', '', NULL, NULL, %s, %s, SYSDATE(), %s)
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
            today_str,
            sponsor_blob
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
        return s_id
    except Exception as err:
        logging.error(f"DB insert failed: {err}")
        return None
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
                        logging.warning(f"skipped SQL chunk due to error: {e}\n{statement.strip()}")
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
    processed, skipped, total_urls, passed = 0, 0, 0, 0
    populate_first = False
    is_senate = None
    a_id = 0
    stopped = False

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

    url_rows = load_pending_urls_from_db(is_senate)  

    client = OpenAI(api_key=getKey())
    seen = set()

    for url_id, url in url_rows:
        canonical = url.strip().rstrip('/')
        if canonical in seen:
            continue
        seen.add(canonical)
        total_urls += 1

        if 'congress.gov' in url and not url.endswith('/text'):
            url += '/text'

        content = getDynamicUrlText(url, is_senate)

        if not content:
            add_note_to_url(url_id, "No content extracted: broken link")
            passed += 1
            continue

        bill_sponsor_blob = extract_sponsor_phrase(content)

        filename_preview, _, _ = callApiWithText(
            text=content,
            client=client,
            url=url,
            is_senate=is_senate,
            filename_only=True  
        )

        if not filename_preview:
            logging.warning(f"Filename preview failed for {url}")
            add_note_to_url(url_id, "Filename preview failed")
            passed += 1
            continue
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM story WHERE filename = %s", (filename_preview,))
        if cursor.fetchone()[0] > 0:
            logging.info(f"Skipping duplicate before GPT call: {filename_preview}")
            add_note_to_url(url_id, "Duplicate filename in story table")
            skipped += 1
            # marking it as processed so that it isnt processed again
            mark_url_processed(url_id)
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

        # print(f"FILENAME: {filename} \n\n HEADLINE: {headline} \n\n PRESS_RELEASE: {press_release}")

        if filename == "STOP":
            stopped = True
            break
        
        if filename == "NA" or not headline or not press_release:
            logging.warning(f"Skipped due to text not being available through api {url}")
            add_note_to_url(url_id, "text not available through api")
            passed += 1
            continue

        if filename and headline and press_release:
            full_text = press_release + f"\n\n* * # * *\n\nPrimary source of information: {url}"
            s_id = insert_story(filename, headline, full_text, a_id, bill_sponsor_blob)
            if s_id:
                mark_url_processed(url_id)
                link_story_to_url(url_id, s_id)
                processed += 1
            else:
                add_note_to_url(url_id, "Story insert failed (possibly DB error)")
                passed += 1

    end_time = datetime.now()
    elapsed = str(end_time - start_time).split('.')[0]
    summary = f"""
Load Version 3.1.2 06/25/2025

Passed Parameters: {' -P' if populate_first else ''} {' -S' if is_senate else ' -H'}
Pull House and Senate: {'Senate' if is_senate else 'House'}

Docs Loaded: {processed}
URLS skipped due to duplication: {skipped}
URLS held for re-evaluation: {passed}
Total URLS looked at: {total_urls}

Stopped Due to Rate Limit: {stopped}

Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Elapsed Time: {elapsed}
"""
    logging.info(summary)
    send_summary_email(summary, is_senate)
    
if __name__ == "__main__":
    main(sys.argv[1:])
