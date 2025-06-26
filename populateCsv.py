import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from db_insert import get_db_connection

def getDynamicBillNumber(url):
    """Extracts the most recent bill number using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=20000)
            page.wait_for_selector("body", timeout=15000)
            page.mouse.move(100, 100)
            page.mouse.wheel(0, 1000)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(3000)

            # Extract bill number from visible page content
            text = BeautifulSoup(page.content(), 'html.parser').get_text()
            if "has not been received" in text:
                return -1

            match = re.search(r'1\.\s*(S\.|H\.R\.)\s*(\d+)', text)
            return int(match.group(2)) if match else -1

        except Exception as e:
            print(f"Error fetching bill number from {url}: {e}")
            return -1
        finally:
            browser.close()

def get_max_bill_number_from_db(chamber):
    """Returns the highest bill number in the database for the given chamber."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT MAX(CAST(REGEXP_SUBSTR(url, '[0-9]+$') AS UNSIGNED))
            FROM url_queue
            WHERE chamber = %s
        """, (chamber,))
        result = cursor.fetchone()[0]
        print(f"{chamber}: MAX BILL NUM => {result}")

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
                print(f"TRYING TO INSERT new {chamber} bill: {num}")
                cursor.execute("""
                    INSERT INTO url_queue (url, chamber, status)
                    VALUES (%s, %s, 'pending')
                """, (url, chamber))
            except Exception as e:
                print(f"Failed to insert {url}: {e}")
        conn.commit()
        print(f"Inserted {latest_number - last_known} new {chamber} bill URLs.")
    finally:
        conn.close()

def populateCsv():
    """Main function to find the latest House and Senate bill numbers and queue missing ones."""
    house_url = "https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%2C%22congress%22%3A119%2C%22chamber%22%3A%22House%22%7D"
    senate_url = "https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%2C%22congress%22%3A119%2C%22chamber%22%3A%22Senate%22%7D"

    house_latest = getDynamicBillNumber(house_url)
    senate_latest = getDynamicBillNumber(senate_url)

    if house_latest != -1:
        current_max_house = get_max_bill_number_from_db("house")
        if house_latest > current_max_house:
            insert_new_bills("house", current_max_house, house_latest)

    if senate_latest != -1:
        current_max_senate = get_max_bill_number_from_db("senate")
        if senate_latest > current_max_senate:
            insert_new_bills("senate", current_max_senate, senate_latest)
