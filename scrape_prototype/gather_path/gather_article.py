import scrapers.content_scraper as content_scraper
from configs.config import program_state
from configs.config import selenium_config
from helpers import format_element
from selenium import webdriver
from helpers.scraper_helper import date_handler
from helpers.gather_helper import gather_description
import web_requests
import logging
import globals
import bs4.element
from unidecode import unidecode


""" Gathers contents for a single article.

Takes AGENCY_DATA dict, article_html tags, webdriver.

This function has two paths depending if 'Landing Page Gather' is True or False.
Unlike the other gather_contents function, this returns the dictionary that contains
the data for the db.

"""


def gather_contents(
    AGENCY_DATA: dict, article_html: bs4.element.Tag, driver: webdriver
) -> dict | None | str:

    article_contents: dict = {}

    landing_page_link = content_scraper.scrape_content(
        AGENCY_DATA["LINK_DATA"], article_html, AGENCY_DATA["AGENCY_ID"], "LINK"
    )

    try:
        if isinstance(landing_page_link, list):
            landing_page_link = landing_page_link[0]

        if landing_page_link.get("href") is None:

            landing_page_link = landing_page_link.find("a")
            if landing_page_link is None:
                logging.error(
                    f"SKIP: landing_page_link.get('href') is giving a 'None' value: {AGENCY_DATA['AGENCY_ID']}"
                )
                return None

        article_link = AGENCY_DATA["URL_PRE"] + landing_page_link.get("href").strip()

    except (TypeError, AttributeError) as err:
        globals.article_link_href_typeerror_none.append(
            f"{AGENCY_DATA['AGENCY_ID']} {AGENCY_DATA['LINK_DATA']}"
        )
        logging.error(
            f"SKIP: landing_page_link.get('href') is giving a 'None' value: {AGENCY_DATA['AGENCY_ID']}\n{err}"
        )
        return None

    article_webpage_html = ""

    # navigating into the article
    if not AGENCY_DATA["LANDING_PAGE_GATHERING"]:

        if AGENCY_DATA["BYPASS"]:
            article_driver = selenium_config()
            article_webpage_html = web_requests.get_website(
                article_link, article_driver, AGENCY_DATA
            )
            article_driver.quit()
            if article_webpage_html is None:
                return None
        else:
            article_webpage_html = web_requests.get_website(
                article_link, driver, AGENCY_DATA
            )
            if article_webpage_html is None:
                return None

    html = (
        article_html if AGENCY_DATA["LANDING_PAGE_GATHERING"] else article_webpage_html
    )

    webpage_titles = content_scraper.scrape_content(
        AGENCY_DATA["TITLE_DATA"], html, AGENCY_DATA["AGENCY_ID"], "TITLE"
    )
    if webpage_titles is None:
        return None

    webpage_titles = format_element.format_title(
        webpage_titles, AGENCY_DATA["TITLE_FORMATTING_DATA"], AGENCY_DATA["AGENCY_ID"]
    )

    if AGENCY_DATA["TITLE_REMOVE"] != "" and AGENCY_DATA["TITLE_REMOVE"] in webpage_titles.text:  # type: ignore
        logging.info(f"SKIP: {AGENCY_DATA['TITLE_REMOVE']} found in title")
        return None

    webpage_dates = content_scraper.scrape_content(
        AGENCY_DATA["DATE_DATA"], html, AGENCY_DATA["AGENCY_ID"], "DATE"
    )

    if webpage_dates is not None:
        # extracting and formatting date, returns INVALID if date is not recent
        if isinstance(webpage_dates, list):
            webpage_dates = webpage_dates[0]
        webpage_dates = date_handler( AGENCY_DATA["DATE_FORMATTING_DATA"], webpage_dates.text)
        if webpage_dates is None:
            globals.date_is_none.append(f"Date is None: {AGENCY_DATA['AGENCY_ID']}")
            return None
        elif webpage_dates == "INVALID":
            return str("INVALID")

    # code duplication to save runtime
    # don't want to enter the article if date is invalid
    if AGENCY_DATA["LANDING_PAGE_GATHERING"]:

        if AGENCY_DATA["BYPASS"]:
            article_driver = selenium_config()
            article_webpage_html = web_requests.get_website(
                article_link, article_driver, AGENCY_DATA
            )
            article_driver.quit()
            if article_webpage_html is None:
                return None
        else:
            article_webpage_html = web_requests.get_website(
                article_link, driver, AGENCY_DATA
            )
            if article_webpage_html is None:
                return None

    article_description = gather_description(AGENCY_DATA, article_webpage_html)
    if article_description is not None:
        article_description = format_element.desc_formatter(
            article_description, AGENCY_DATA
        )

    article_contents["title"] = unidecode(webpage_titles)
    article_contents["date"] = webpage_dates
    article_contents["desc"] = article_description
    article_contents["a_id"] = AGENCY_DATA["AGENCY_ID"]
    article_contents["url"] = article_link

    for key in article_contents:
        if article_contents[key] is None:
            return None

    # used for debugging the outputs
    if program_state["test_run"]:
        logging.debug(f"Titles: {article_contents['title']}")
        logging.debug(f"Dates: {article_contents['date']}")
        logging.debug(f"Desc: {article_contents['desc']}")
        logging.debug(f"Agency_id {article_contents['a_id']}")
        logging.debug(f"Article Link: {article_contents['url']}")

    return article_contents
