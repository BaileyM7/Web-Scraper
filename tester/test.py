import re
import csv

# Load bill numbers from filenames (e.g., s1093 or hr101)
def load_filenames(filename_csv):
    bill_numbers = set()
    with open(filename_csv, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for cell in row:
                # Extract s#### and hr### bill numbers
                match_s = re.search(r'-s(\d+)', cell, re.IGNORECASE)
                match_hr = re.search(r'-hr(\d+)', cell, re.IGNORECASE)
                if match_s:
                    bill_numbers.add(match_s.group(1))
                if match_hr:
                    bill_numbers.add(match_hr.group(1))
    return bill_numbers

# Check each URL and print if the trailing bill number is not found in the filename numbers
def check_urls(urls_csv, filename_numbers):
    with open(urls_csv, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for url in row:
                # Match both /senate-bill/#### and /house-bill/####
                match = re.search(r'/(?:senate|house)-bill/(\d+)', url)
                if match:
                    bill_number = match.group(1)
                    if bill_number not in filename_numbers:
                        print(url.strip())

# Replace with your actual CSV file paths
filename_csv = 'filenames.csv'
urls_csv = 'urls.csv'

filename_numbers = load_filenames(filename_csv)
check_urls(urls_csv, filename_numbers)
