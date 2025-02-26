from selenium.common.exceptions import WebDriverException, TimeoutException
from urllib3.exceptions import ReadTimeoutError
from selenium import webdriver
from bs4 import BeautifulSoup
from typeguard import typechecked
from configs.config import program_state
from requests.exceptions import RequestException
import cloudscraper.exceptions
import cloudscraper
import bs4
import time
import random
import globals
import configs.config as config
import logging


# get_website handles the standard procedure for gathering the landing page source code
# returns website_html_data or None if the process failed
# @typechecked
def get_website(
    url: str, driver: webdriver, AGENCY_DATA: dict
) -> bs4.BeautifulSoup | None:

    # load time to be set
    load_time: int | float = 0

    # trying to fix connection errors
    max_retries = 3
    backoff_factor = 2

    attempt = 0
    while attempt < max_retries:

        try:
            # passing the url to the webdriver
            driver.get(url)

            # checking to see if this url needs a different load time than default
            load_time = (
                program_state["DEFAULT_LOAD_TIME"]
                if len(AGENCY_DATA["LOAD_TIME"]) == 0
                else int(AGENCY_DATA["LOAD_TIME"])
            )

            logging.info(f"Driver opened url {url}: {load_time} second load started")
            time.sleep(load_time)

            # gathering the source code from page
            web_request_info = driver.page_source
            webpage_html: bs4.BeautifulSoup = BeautifulSoup(web_request_info, "html.parser")

            return webpage_html

        except (TimeoutException, WebDriverException, ReadTimeoutError) as err:
            attempt += 1
            wait_time = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, 1)
            logging.error(f"Attempt {attempt} failed: {err}. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)

        except (IndexError, ValueError) as err:
            logging.error(f"SKIPPING: Invalid load time field...\t{err}")
            globals.invalid_load_time.append(f"{AGENCY_DATA['AGENCY_ID']}: {load_time}")
            return None

        except WebDriverException as err:
            logging.error(f"Web Driver failed to access url: {err}")
            globals.failed_access.append(f"{AGENCY_DATA['AGENCY_ID']}: {url}")
            return None
    logging.error("All retries failed, skipping url")
    return None


# @typechecked
def cloudscrape_website(url: str, AGENCY_DATA: dict) -> bs4.BeautifulSoup | None:
    try:
        web_request_info = cloudscraper.create_scraper().get(url)

        if "403" in str(web_request_info):
            logging.error(f"SKIPPING: 403 from url: {url}")
            globals.failed_access_403.append(f"{AGENCY_DATA['AGENCY_ID']}: {url}")
            return None

        webpage_html = BeautifulSoup(web_request_info.text, "html.parser")
        return webpage_html

    except RequestException as err:
        logging.error(f"SKIPPING: cloudscraper failed to resolve {url}\t{err}")
        globals.cloud_scrapper_error.append(f"{AGENCY_DATA['AGENCY_ID']}: {url}")
