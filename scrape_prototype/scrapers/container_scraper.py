from helpers.scraper_helper import data_finder, format_slice
from typeguard import typechecked
from bs4 import BeautifulSoup
import bs4.element
import logging


# get_containers gathers article containers from landing page
# @typechecked
def get_containers(
    container_data: str, webpage_html: bs4.BeautifulSoup | bs4.element.Tag
) -> bs4.element.Tag | list[bs4.element.Tag] | None:

    html: bs4.BeautifulSoup | bs4.element.Tag | list[bs4.element.Tag] = webpage_html
    slicer = slice(None)

    # gathering data from link csv field
    container_data_list = container_data.split("~")

    # looping through the container list to get most specific container
    for container in container_data_list:
        field_split = container.split("|")
        # destructuring list into constants
        try:
            FIND_ALL, HTML_ATTRIBUTE, CONTAINER_NAME, *SLICING_DATA = field_split # type: ignore

            IS_ELEM: bool = HTML_ATTRIBUTE == "elem"
            IS_SLICING: bool = len(SLICING_DATA) > 0
            FIND_ALL: bool = FIND_ALL == "find_all"

        except ValueError as err:
            # error happens when theres an empty field or not enough fields
            logging.error(f"SKIPPING: Invalid number of link fields in csv: {err}")
            return None

        # you cannot find a single tag and try to slice at the same time
        if IS_SLICING and not FIND_ALL:
            logging.error(
                "SKIPPING: cannot slice on a 'find' call, did you mean find_all?"
            )
            return None

        # checking to see if the data needs slicing
        if IS_SLICING:
            SLICING = format_slice(SLICING_DATA)
            slicer = slice(*SLICING)

        html = data_finder(
            IS_ELEM, FIND_ALL, HTML_ATTRIBUTE, CONTAINER_NAME, slicer, html # type: ignore
        )
        if html is None:
            logging.error("Html is none")
            return None

    return html
