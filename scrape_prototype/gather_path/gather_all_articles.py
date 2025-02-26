import scrapers.content_scraper as content_scraper
import scrapers.container_scraper as container_scraper
from configs.config import selenium_config
from globals import invalid_dates
import globals
from helpers import format_element
from helpers.scraper_helper import date_handler
from helpers.gather_helper import gather_description
from configs.config import program_state
from selenium import webdriver
import db.storage as storage
from unidecode import unidecode
import web_requests
import bs4.element
import logging


""" Gathers contents for all articles.

Takes AGENCY_DATA dict, article_html tags, webdriver, db_data.

This function has two paths depending if 'Landing Page Gather' is True or False.
Unlike the other gather_contents function, this transfers data right into the database
and doesn't return unless there is a failure.

"""


def gather_contents(
    AGENCY_DATA: dict, article_html: bs4.element.Tag, db_data: dict, driver: webdriver
):
    article_contents = {}

    # checking if data should be gathered before traversing article link
    if not AGENCY_DATA["LANDING_PAGE_GATHERING"]:

        # gathering all links on landing page
        landing_page_link: bs4.ResultSet = content_scraper.scrape_content(
            AGENCY_DATA["LINK_DATA"], article_html, AGENCY_DATA["AGENCY_ID"], "LINK"
        )

        invalid_counter = 0

        # parsing through each link
        for link in landing_page_link:

            if invalid_counter > invalid_dates:
                break

            # !Bug Potential
            # TODO create a error handler that skips if href isn't found
            # Will only work if first <a> under container class if the correct href
            if link.get("href") is None:
                logging.debug("finding")
                link = link.find("a")

            try:
                article_link = AGENCY_DATA["URL_PRE"] + link.get("href").strip()
            except TypeError:
                logging.error(
                    f"SKIP: landing_page_link.get('href') is giving a 'None' value: {AGENCY_DATA['AGENCY_ID']}"
                )
                return None

            article_webpage_html = ""

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


            webpage_titles = content_scraper.scrape_content(
                AGENCY_DATA["TITLE_DATA"],
                article_webpage_html,
                AGENCY_DATA["AGENCY_ID"],
                "TITLE",
            )

            webpage_titles = format_element.format_title(
                webpage_titles,
                AGENCY_DATA["TITLE_FORMATTING_DATA"],
                AGENCY_DATA["AGENCY_ID"],
            )

            if webpage_titles is None:
                globals.title_is_none.append(f"None Title: {AGENCY_DATA['AGENCY_ID']}")
                return None


            webpage_dates = content_scraper.scrape_content(
                AGENCY_DATA["DATE_DATA"],
                article_webpage_html,
                AGENCY_DATA["AGENCY_ID"],
                "DATE",
            )

            # extracting and formatting date, returns INVALID if date is not recent
            if webpage_dates is not None:
                webpage_dates = date_handler(
                    AGENCY_DATA["DATE_FORMATTING_DATA"], webpage_dates.text
                )
                if webpage_dates is None:
                    continue
                elif webpage_dates == "INVALID":
                    invalid_counter += 1
                    continue

            article_description = gather_description(AGENCY_DATA, article_webpage_html)
            if article_description is not None:
                article_description = format_element.desc_formatter(
                    article_description, AGENCY_DATA
                )

            # inserting data into dict
            article_contents["title"] = unidecode(webpage_titles)
            article_contents["date"] = webpage_dates
            article_contents["desc"] = article_description
            article_contents["a_id"] = AGENCY_DATA["AGENCY_ID"]
            article_contents["url"] = article_link

            # checking to see if nothing was scraped for any elements
            for key in article_contents:
                if article_contents[key] is None:
                    return None

            # inserting data into the db
            storage.db_insert(db_data, article_contents)

    else:

        webpage_titles = content_scraper.scrape_content(
            AGENCY_DATA["TITLE_DATA"],
            article_html,
            AGENCY_DATA["AGENCY_ID"],
            "TITLE",
        )
        if webpage_titles is None:
            globals.title_is_none.append(f"None Title: {AGENCY_DATA['AGENCY_ID']}")
            return None

        webpage_dates = content_scraper.scrape_content(
            AGENCY_DATA["DATE_DATA"],
            article_html,
            AGENCY_DATA["AGENCY_ID"],
            "DATE",
        )
        if webpage_dates is None:
            globals.date_is_none.append(f"None Date: {AGENCY_DATA['AGENCY_ID']}")
            return None

        landing_page_link: bs4.ResultSet = content_scraper.scrape_content(
            AGENCY_DATA["LINK_DATA"], article_html, AGENCY_DATA["AGENCY_ID"], "LINK"
        )
        if landing_page_link is None:
            globals.link_is_none.append(f"None Link: {AGENCY_DATA['AGENCY_ID']}")
            return None

        # handles case if the number of elements selected aren't the same
        if not len(webpage_titles) == len(webpage_dates) == len(landing_page_link):  # type: ignore
            logging.error("SKIP GATHER: Number of article elements need to be the same")
            logging_string = f"Titles: {len(webpage_titles)} Dates: {len(webpage_dates)} Links: {len(landing_page_link)}"  # type: ignore
            logging.error(logging_string)
            globals.unequal_titles_dates_links_counts.append(
                f"{AGENCY_DATA['AGENCY_ID']}: {logging_string}"
            )
            return None

        # keeps track of the amount of invalid dates a website has
        invalid_counter = 0

        # parsing each title, date, and link at once
        for title, date, link in zip(webpage_titles, webpage_dates, landing_page_link):

            if invalid_counter > invalid_dates:
                break

            if link.get("href") is None:
                link = link.find("a")

            try:
                article_link = AGENCY_DATA["URL_PRE"] + link.get("href").strip()
            except TypeError:
                logging.error(
                    f"SKIP: landing_page_link.get('href') is giving a 'None' value: {AGENCY_DATA['AGENCY_ID']}"
                )
                return None

            title = format_element.format_title(
                title,
                AGENCY_DATA["TITLE_FORMATTING_DATA"],
                AGENCY_DATA["AGENCY_ID"],
            )

            # extracting and formatting date, returns INVALID if date is not recent
            if webpage_dates is not None:
                date = date_handler(AGENCY_DATA["DATE_FORMATTING_DATA"], date.text)
                if date is None:
                    continue
                elif date == "INVALID":
                    invalid_counter += 1
                    continue

            article_webpage_html = ""

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

            # inserting data into dict
            article_contents["title"] = unidecode(title)
            article_contents["date"] = date
            article_contents["desc"] = article_description
            article_contents["a_id"] = AGENCY_DATA["AGENCY_ID"]
            article_contents["url"] = article_link

            # checking to see if nothing was scraped for any elements
            for key in article_contents:
                if article_contents[key] is None:
                    return None

            # inserting data into the db
            storage.db_insert(db_data, article_contents)
