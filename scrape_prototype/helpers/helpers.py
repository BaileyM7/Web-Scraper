from configs.config import program_state
from typeguard import typechecked
import globals
import time
import logging
from selenium import webdriver
import random
from selenium.webdriver.common.action_chains import ActionChains

# LOGGING

# check the a_id against the uname before continuing
# if test_run is true than we don't want to check against uname
# @typechecked
def get_uname(AGENCY_DATA: dict, unames: dict) -> str | None:
    try:
        if not program_state["test_run"]:
            return unames[AGENCY_DATA["AGENCY_ID"]]
        return "test_uname"
    except:
        globals.no_uname_found.append(
            f"{AGENCY_DATA['AGENCY_ID']}: {AGENCY_DATA['FULL_URL']}"
        )
        logging.error(
            f"** SKIPPING uname for a_id: {AGENCY_DATA['AGENCY_ID']} not found."
        )

        return None


# check the a_id against the ledes before continuing
# if test_run is true than we don't want to check against ledes
# @typechecked
def get_lede(article_contents: dict, ledes: dict) -> str | None:
    try:
        if not program_state["test_run"]:
            return ledes[article_contents["a_id"]]
        return "testlede"
    except:
        globals.no_lead_found.append(
            f"{article_contents['a_id']}: {article_contents['url']}"
        )
        logging.error(
            f"** SKIPPING lede for a_id: {article_contents['a_id']} not found."
        )
        return None


# get_filename creates and returns the unique filename for the article being loaded
# @typechecked
def get_filename(filenames: dict, article_contents: dict) -> str | None:
    try:
        if not program_state["test_run"]:
            date = article_contents['date'].replace("-", "")[2:]
            filename = f"$H {filenames[article_contents['a_id']]}{date}{article_contents['title'][-10:]}"
            return filename
        return f"testfilename {article_contents['title'][-10:]}"
    except:
        globals.filename_creation_error.append(f"{article_contents['a_id']}: {article_contents['url']}")
        logging.error(f"Filename creation error: {article_contents['a_id']}")
        return None


# applying a small program delay for senate sites
@typechecked
def program_sleep(pull_senate: bool, sleep_seconds: int, specific_id: str):
    if not program_state["test_run"] and pull_senate:
        if len(specific_id) == 0:
            logging.info(f"*** {sleep_seconds} SECOND PROGRAM DELAY ***")
            time.sleep(sleep_seconds)

# short function that provides varability in scrape to similate human activity
def simulate_human_activity(driver):

    for _ in range(random.randint(3, 7)):
        scroll_amount = random.randint(200, 800)
        direction = random.choice([-1, 1])
        driver.execute_script(f"window.scrollBy(0, {direction * scroll_amount});")
        time.sleep(random.uniform(0.5, 2))
