import re

def convert_bill_dates(text):
    pattern = r"Introduced in (?:Senate|House) \((\d{2})/(\d{2})/(\d{4})\)"
    
    match = re.search(pattern, text)
    if match:
        mm, dd, yyyy = match.groups()
        return f"{yyyy[-2:]}{mm}{dd}"
    return None

# Example usage
text = "This bill was Introduced in Senate (01/16/2025)."
updated_date = convert_bill_dates(text)
print(updated_date)
