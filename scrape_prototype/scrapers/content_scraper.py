from helpers.scraper_helper import data_finder, format_slice
from typeguard import typechecked
from bs4 import BeautifulSoup
import bs4.element
import logging
import globals


# gather_links scrapes the links from the landing page
# agency id allows for better error logs of who gave an error
# error callers is given either LINK TITLE or DATE to log errors acordingly
# @typechecked
def scrape_content(
    CONTENT_DATA: str,
    webpage_html: bs4.element.Tag | bs4.element.PageElement,
    AGENCY_ID: str,
    error_caller: str,
) -> bs4.element.Tag | list[bs4.element.Tag] | None:

    # variable that contains the content data
    element_tags: bs4.element.Tag | list[bs4.element.Tag] | None
    slicer: slice = slice(None)

    # checks for alternate data field
    alternate_data = CONTENT_DATA.split("<>")
    for data in alternate_data:

        # gathering data from csv field
        link_data_list: list[str] = data.split("|")

        # destructuring list into constants
        try:
            FIND_ALL, HTML_ATTRIBUTE, CONTAINER_NAME, *SLICING_DATA = link_data_list

            IS_ELEM: bool = HTML_ATTRIBUTE == "elem"
            IS_SLICING: bool = len(SLICING_DATA) > 0
            FIND_ALL: bool = FIND_ALL == "find_all"

        except ValueError as err:
            # error happens when theres an empty field or not enough fields
            logging.error(
                f"{error_caller} {AGENCY_ID} SKIP: Invalid number of data fields in csv: {err}"
            )
            return None

        # you cannot find a single tag and try to slice at the same time
        if IS_SLICING and not FIND_ALL:
            logging.error(
                f"{error_caller} {AGENCY_ID}: cannot slice on a 'find' call, did you mean find_all?"
            )
            return None

        # checking to see if the data needs slicing
        if IS_SLICING:
            SLICING = format_slice(SLICING_DATA)
            if SLICING == None:
                return None
            slicer = slice(*SLICING)

        # parsing the html data based on the csv fields
        element_tags = data_finder(
            IS_ELEM, FIND_ALL, HTML_ATTRIBUTE, CONTAINER_NAME, slicer, webpage_html
        )

        # exiting loop because data was found
        if element_tags != None and len(element_tags) != 0:
            break

    # this is implying the content search failed
    if (
        element_tags is None or len(element_tags) == 0
    ) and error_caller != "DESC REMOVAL":
        logging.error(f"{error_caller} {AGENCY_ID} SKIP: No content was gathered")
        globals.element_not_found.append(f"{AGENCY_ID} {error_caller} ERROR")
        return None

    return element_tags
