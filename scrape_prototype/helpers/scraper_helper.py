from typeguard import typechecked
from configs.config import program_state
import logging
from datetime import datetime
from datetime import timedelta
import datefinder
import dateparser
import bs4.element
from dateutil import parser
from dateutil.parser import ParserError
import globals
import re


# data_finder parses html based on csv arguments provided
# @typechecked
def data_finder(
    IS_ELEM: bool,
    FIND_ALL: bool,
    HTML_ATTRIBUTE: str,
    CONTAINER_NAME: str,
    slicer: slice,
    html: bs4.BeautifulSoup | bs4.element.Tag,
):

    if not IS_ELEM:
        attribute = {HTML_ATTRIBUTE: CONTAINER_NAME}
        data = (
            html.find_all(attrs=attribute)[slicer]
            if FIND_ALL
            else html.find(attrs=attribute)
        )
    else:
        data = (
            html.find_all(CONTAINER_NAME)[slicer]
            if FIND_ALL
            else html.find(CONTAINER_NAME)
        )
    if data is None or data == -1:
        return None

    return data  # type: ignore


# taking the strings from the csv and converting them to an int
# not converting to int if None is found
@typechecked
def format_slice(SLICING_DATA):
    SLICING = []
    try:
        for data in SLICING_DATA:
            if "None" in data:
                SLICING.append(None)
            else:
                SLICING.append(int(data))
    except ValueError as err:
        logging.debug(err)
        return None

    return SLICING


# date_cleaner extracting date from text if needed and checks validity
def date_handler(DATE_FORMATTING_DATA: str, date: str) -> str | None:

    extracted_date = ""

    # this is initally a spec case for a site but could be used blanketly
    month_map = {
        " january ": "/01/",
        " february ": "/02/",
        " march ": "/03/",
        " april ": "/04/",
        " may ": "/05/",
        " june ": "/06/",
        " july ": "/07/",
        " august ": "/08/",
        " september ": "/09/",
        " october ": "/10/",
        " november ": "/11/",
        " december ": "/12/",
    }

    # dict of weaknesses that the datefinder has
    # trying to format the date beforehand to avoid its weaknesses
    date_format = {
        "yesterday": datetime.strftime(datetime.now() - timedelta(days=1), "%b/%d/%Y"),
        "hours ago": datetime.strftime(datetime.now(), "%b/%d/%Y"),
        "today": datetime.strftime(datetime.now(), "%b/%d/%Y"),
        "minutes ago": datetime.strftime(datetime.now(), "%b/%d/%Y"),
    }

    date = date.lower()
    for key in date_format:
        if key in date:
            date = date_format[key]

    for month, number in month_map.items():
        date = date.replace(month, number)

    # replacing large amounts of whitespace embedded in date element
    date = re.sub("\s\s*", " ", date)

    # datefinder struggles with understanding 'Sept' for September dates
    if "sept" in date and "september" not in date:
        date = date.replace("sept", "sep")

    # "swap" keyword is temporary
    # if keyword is detected, it will scrape dates that have the day before the month
    if DATE_FORMATTING_DATA == "swap":
        try:
            extracted_date = parser.parse(date, dayfirst=True)
        except ParserError as err:
            logging.error(f"Date Parser Failed: {date} - {err}")
            return None

    # handles keyword replacing in csv field
    elif DATE_FORMATTING_DATA != "":
        date = date.replace(DATE_FORMATTING_DATA, "")
        extracted_date = next(datefinder.find_dates(date), None)
        if extracted_date is None:
            logging.error(f"Date Extraction failed: {date}")
            return None

    else:
        extracted_date = next(datefinder.find_dates(date), None)
        if extracted_date is None:
            logging.error(f"Date Extraction failed: {date}")
            return None

    # checking how many days ago the date is
    days = (datetime.now() - extracted_date).days
    if days <= program_state["amount_of_days"] and days >= -7:
        return extracted_date.strftime("%Y-%m-%d")

    logging.info(f"INVALID DATE: {extracted_date}")
    return "INVALID"
