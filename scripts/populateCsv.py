from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import csv

def getDynamicUrlText(url):
    """Extracts the most recent bill number from a dynamically loaded web page using Playwright in stealth headless mode."""
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
            try:
                page.wait_for_selector("body", timeout=15000)
            except:
                print("Main selector did not load — returning -1")
                return -1

            # Simulate human interaction
            page.mouse.move(100, 100)
            page.mouse.wheel(0, 1000)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(3000)

            # Parse page content
            text = BeautifulSoup(page.content(), 'html.parser').get_text()

            if "has not been received" in text:
                return -1

            # Use regex to find most recent bill number
            match = re.search(r'1\.\s*(S\.|H\.R\.)\s*(\d+)', text)
            if match:
                bill_number = match.group(2)
                print(f"Extracted Bill Number: {bill_number}")
                return int(bill_number)
            else:
                print("No bill number found.")
                return -1

        except Exception as e:
            print(f"Error fetching dynamic content: {e}")
            return -1
        finally:
            browser.close()

def updateLastFoundAndAppendToCSV(file_path, house_number, senate_number):
    """Updates last found bill numbers and appends new range to house.csv."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            last_house = int(lines[0].strip())
            last_senate = int(lines[1].strip())
    except FileNotFoundError:
        last_house, last_senate = 0, 0
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    if house_number > last_house:
        with open("csv/house.csv", 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for num in range(last_house + 1, house_number + 1):
                csv_writer.writerow([f'https://www.congress.gov/bill/119th-congress/house-bill/{num}'])

    if senate_number > last_senate:
        with open("csv/senate.csv", 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for num in range(last_senate + 1, senate_number + 1):
                csv_writer.writerow([f'https://www.congress.gov/bill/119th-congress/senate-bill/{num}'])
    
    with open(file_path, 'w') as file:
        file.write(f"{house_number}\n{senate_number}\n")

house_url = "https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%2C%22congress%22%3A119%2C%22chamber%22%3A%22House%22%7D"
senate_url = "https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%2C%22congress%22%3A119%2C%22chamber%22%3A%22Senate%22%7D"

house_number = getDynamicUrlText(house_url)
senate_number = getDynamicUrlText(senate_url)

if house_number != -1 and senate_number != -1:
    updateLastFoundAndAppendToCSV("lastFound.txt", house_number, senate_number)
