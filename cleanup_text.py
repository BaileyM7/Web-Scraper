import re
import logging
from datetime import datetime

def cleanup_text(text, write=False):
    # Define byte-replacement mappings
    replacements = {
        b"\xce\xbc": "u",  # μ
        b"\xc2\x9d": "",
        b"\xc2\xa0": " ",  # non-breaking space
        b"\xc2\xa1": "i",  # ¡
        b"\xc2\xa2": "cents",  # ¢
        b"\xc2\xa3": "pound sterling",  # £
        b"\xc2\xa4": "#",  # ¤
        b"\xc2\xa5": "Yen",  # ¥
        b"\xc2\xa7": "Sec.",  # §
        b"\xc2\xa8": "~",  # ¨
        b"\xc2\xa9": " Copyright (c) ",  # ©
        b"\xc2\xaa": "(a)",  # ª
        b"\xc2\xab": "<<",  # «
        b"\xc2\xac": " ",  # ¬
        b"\xc2\xad": "",  # soft hyphen
        b"\xc2\xae": "(R)",  # ®
        b"\xc2\xaf": "",
        b"\xc2\xb0": " degrees",  # °
        b"\xc2\xb1": "+-",  # ±
        b"\xc2\xb2": "(2)",  # ²
        b"\xc2\xb3": "(3)",  # ³
        b"\xc2\xb4": "'",  # ´
        b"\xc2\xb5": "u",  # µ
        b"\xc2\xb6": "\n",  # ¶
        b"\xc2\xb7": ".",  # ·
        b"\xc2\xb9": "(1)",  # ¹
        b"\xc2\xba": "-",  # º
        b"\xc2\xbb": '"',  # »
        b"\xc2\xbc": "1/4",
        b"\xc2\xbd": "1/2",
        b"\xc2\xbe": "3/4",
        b"\xc2\xbf": "",  # ¿
        b"\xca\xbb": "",  # ʻ from Hawaiʻi
        b"\xe2\x80\x82": "",
        b"\xe2\x80\x8a": " ",
        b"\xe2\x80\x93": "-",  # –
        b"\xe2\x80\x94": "--",  # —
        b"\xe2\x80\x98": "'",  # ‘
        b"\xe2\x80\x99": "'",  # ’
        b"\xe2\x80\x9c": '"',  # “
        b"\xe2\x80\x9d": '"',  # ”
        b"\xe2\x80\xa6": "...",  # …
        b"\xe2\x80\xa2": "-",  # •
        b"\xe2\x82\xac": "Euros",  # €
        b"\xe2\x84\xa2": "(TM)",  # ™
        b"\xe2\x86\x90": "<-",  # ←
        b"\xe2\x86\x92": "->",  # →
        b"\xe2\x87\x90": "<->",  # ⇐
        b"\xe2\x88\x92": "-",  # −
        b"\xe2\x81\x84": "/",  # ⁄
        b"\xe2\x9c\x93": "check",  # ✓
        b"\xa7\xa7\xa7\xa7": "sections ",
        b"\xa7\xa7": "section ",
    }

    # Add all your other replacements here following the same format...
    # This would typically be built dynamically from a large PHP array if needed

    # Convert text to bytes
    raw_bytes = text.encode('utf-8')

    # Apply all replacements
    for bad, good in replacements.items():
        raw_bytes = raw_bytes.replace(bad, good.encode('ascii', 'ignore'))

    # Convert back to string
    text = raw_bytes.decode('ascii', 'ignore')

    # Optional: log bad characters
    normal_characters = re.compile(r"[a-zA-Z0-9\s`~!@#$%^&*()_+\-={}|:;<>?,./\"'\\\[\]]")
    bad_chars = ''.join([char for char in text if not normal_characters.match(char)])
    
    if bad_chars:
        bad_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        logging.basicConfig(filename="/tnsdata/logs/badchars1", level=logging.ERROR, format="%(message)s")
        logging.error(f"\n{bad_time} - [{bad_chars}]")

    return text

