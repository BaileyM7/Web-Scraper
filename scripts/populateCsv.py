from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import csv

def getDynamicUrlText(url):
    """Extracts text from a dynamically loaded web page using Playwright and extracts the bill number."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=20000)
            page.wait_for_timeout(5000)
            page.mouse.move(100, 100)
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(3000)

            text = BeautifulSoup(page.content(), 'html.parser').get_text()

            if "has not been received" in text:
                return -1
            
            # Improved regex to handle normal and non-breaking spaces
            match = re.search(r'1\.\s*(S\.|H\.R\.)\s*(\d+)', text)
            if match:
                bill_number = match.group(2)  # Extract the number part
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
        with open("../csv/house.csv", 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for num in range(last_house + 1, house_number + 1):
                csv_writer.writerow([f'https://www.congress.gov/bill/119th-congress/house-bill/{num}'])

    if senate_number > last_senate:
        with open("../csv/senate.csv", 'a', newline='') as csvfile:
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
