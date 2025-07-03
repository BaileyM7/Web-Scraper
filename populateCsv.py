import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from db_insert import get_db_connection
import logging
from url_processing import get_most_recent_bill_number

'''
def getDynamicBillNumber(url):
    """Extracts the most recent bill number from a Congress.gov search page using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            java_script_enabled=True
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=20000)

            # Scroll to ensure lazy content loads
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(1000)
                page.keyboard.press("ArrowDown")

            # Wait for the first bill link to appear
            selector = "#main > ol > li:nth-child(1) > span.result-heading > a"
            try:
                page.wait_for_selector(selector, timeout=35000)
            except:
                logging.debug(f"Bill result not found: {url}")
                return -1

            # Extract and parse bill number from the result
            bill_text = page.locator(selector).inner_text()
            logging.debug(f"Raw bill text: {bill_text}")

            match = re.search(r'(S\.|H\.R\.)\s*(\d+)', bill_text)
            if match:
                bill_number = int(match.group(2))
                logging.debug(f"MOST RECENT NUMBER FOUND: {bill_number}")
                return bill_number
            else:
                logging.debug(f"No bill number match in: {url} (text was: '{bill_text}')")
                return -1

        except Exception as e:
            logging.debug(f"Error fetching bill number from {url}: {e}")
            return -1

        finally:
            browser.close()
'''

def get_max_bill_number_from_db(chamber):
    """Returns the highest bill number in the database for the given chamber."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING_INDEX(url, '/', -1) AS UNSIGNED))
            FROM url_queue
            WHERE chamber = %s
        """, (chamber,))
        result = cursor.fetchone()[0]
        logging.debug(f"{chamber}: MAX CURRENT BILL NUM => {result}")

        return result if result else 0
    finally:
        conn.close()

def insert_new_bills(chamber, last_known, latest_number):
    """Inserts new bill URLs into the queue based on the difference between latest and known max."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        base_url = f"https://www.congress.gov/bill/119th-congress/{chamber}-bill/"
        for num in range(last_known + 1, latest_number + 1):
            url = base_url + str(num)
            try:
                logging.debug(f"TRYING TO INSERT new {chamber} bill: {num}")
                cursor.execute("""
                    INSERT INTO url_queue (url, chamber, status)
                    VALUES (%s, %s, 'pending')
                """, (url, chamber))

                logging.debug(f"Insert success: {url}")
            except Exception as e:
                logging.debug(f"Failed to insert {url}: {e}")
        conn.commit()
        logging.debug(f"Inserted {latest_number - last_known} new {chamber} bill URLs.")
    finally:
        conn.close()

def populateCsv():
    """Main function to find the latest House and Senate bill numbers and queue missing ones."""

    house_latest = get_most_recent_bill_number(False)
    senate_latest = get_most_recent_bill_number(True)
    
    if house_latest != -1:
        current_max_house = get_max_bill_number_from_db("house")
        if house_latest > current_max_house:
            insert_new_bills("house", current_max_house, house_latest)

    if senate_latest != -1:
        current_max_senate = get_max_bill_number_from_db("senate")
        if senate_latest > current_max_senate:
            insert_new_bills("senate", current_max_senate, senate_latest)
