#!/usr/bin/python3
from configs.my_mail import my_mail
import scrapers.container_scraper as container_scraper
import gather_path.gather_article as gather_article
import gather_path.gather_all_articles as gather_all_articles
import db.storage as storage
from configs.config import program_state
import configs.config as config
from csv_validator import csv_validate
import web_requests
from datetime import datetime
import globals
import helpers.helpers as helpers
import csv
import getopt
import sys
import logging
import yaml
import time
import re

# tracking times for logging purposes
start = datetime.now()
# selenium webdriver
driver = config.selenium_config()

# getopt setup
try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "d:i:PST",
        ["id", "days", "production", "house_and_senate", "test"],
    )
except getopt.GetoptError as err:
    print(err)
    # usage exit
    sys.exit(2)

for o, val in opts:
    if o == "-i":
        program_state["specific_id"] = val
        globals.single_id = int(val)
    if o == "-P":
        program_state["production_run"] = True
        program_state["amount_of_days"] = 1
        program_state["lede_filter"] = "M-%"
    if o == "-d":
        program_state["amount_of_days"] = int(val)
    if o == "-S":
        program_state["pull_house_and_senate"] = True
    if o == "-T":
        program_state["test_run"] = True

# sets up the logger for information and testing purposes
config.log_config()

# opens up yaml file to auth user and use database
with open("./configs/db_config.yml", "r") as yml_file:
    yml_config = yaml.load(yml_file, Loader=yaml.FullLoader)

db_data = {}

db_data["yml_config"] = yml_config

# sql database connection
db_data["database"] = config.db_config(yml_config)

# objects that let you interact with different queries
# db_data["press_release_cursor"] = db_data["database"].cursor()
agency_cursor = db_data["database"].cursor()

# main query
query: str = config.query_config(yml_config, program_state["lede_filter"])
agency_cursor.execute(query)

# gathering info from database
db_data["filenames"] = {}
db_data["ledes"] = {}
unames = {}
for f in agency_cursor:
    db_data["filenames"][str(f[0])] = f[1]
    db_data["ledes"][str(f[0])] = str(f[2])
    unames[str(f[0])] = str(f[3])

# closing connection until insertion is necessary
db_data["database"].close()

# insert statement that takes: headline, date, body text, article id, box status, filename, headline 2, uname
db_data[
    "SQL_INSERT"
] = """
INSERT INTO tns.press_release (headline,content_date,body_txt,a_id,status,create_date,last_action,filename,headline2, uname) VALUES ( %s, %s, %s, %s, %s, SYSDATE(),SYSDATE(),%s, %s, %s)
"""

csv_validate("./configs/" + config.CSV_FILE)

# Open the csv file for reading
with open("./configs/" + config.CSV_FILE, "r") as agency_data:
    # A single line of the csv
    agency_row = csv.reader(agency_data)

    # Skips the key for the csv
    next(agency_row)
    counter = 0

    for data_field in agency_row:

        # validates csv before continuing
        counter += 1
        # checks validation before running
        # skips bad ones and logs
        if csv_validate(data_field) is None:
            logging.error(f"CSV line {counter} is invalid")
            globals.csv_line_error.append(str(counter))
            continue

        # !Index fields are subject to change
        # Assigning a constant for each field of the csv
        AGENCY_DATA = {
            "AGENCY_ID": data_field[0],
            "URL_FIELD": data_field[1],
            "ARTICLE_CONTAINERS": data_field[2],
            "LANDING_PAGE_GATHERING": data_field[3],
            "LINK_DATA": data_field[4],
            "TITLE_DATA": data_field[5],
            "TITLE_REMOVE": data_field[6],
            "DATE_DATA": data_field[7],
            "DESCRIPTION_DATA": data_field[8],
            "DESC_REMOVE_DATA": data_field[9],
            "TITLE_FORMATTING_DATA": data_field[10],
            "DATE_FORMATTING_DATA": data_field[11],
            "LOAD_TIME": data_field[12],
            "BYPASS": data_field[13],
            "STATUS": data_field[14],
        }

        # Retrieving specific url data from csv field
        url_field_split = AGENCY_DATA["URL_FIELD"].split("|")
        AGENCY_DATA["FULL_URL"] = url_field_split[0]
        AGENCY_DATA["URL_PRE"] = "" if len(url_field_split) < 2 else url_field_split[1]
        AGENCY_DATA["LANDING_PAGE_GATHERING"] = (
            True if AGENCY_DATA["LANDING_PAGE_GATHERING"] == "True" else False
        )

        # if find_all is in one of the fields, we need to use a different path
        single_gather = (
            True if "find_all" in AGENCY_DATA["ARTICLE_CONTAINERS"] else False
        )

        # Used to only gather a single agency via id
        if (
            len(program_state["specific_id"]) != 0
            and AGENCY_DATA["AGENCY_ID"] != program_state["specific_id"]
        ):
            # not necesccary to capture skipping data for email output
            logging.info(f"Skipping {AGENCY_DATA['AGENCY_ID']}")
            continue

        # Skipping house and senate when running standard pull
        if (
            re.search(".house.gov", AGENCY_DATA["URL_FIELD"])
            or re.search(".senate.gov", AGENCY_DATA["URL_FIELD"])
        ) and not program_state["pull_house_and_senate"]:
            if len(program_state["specific_id"]) == 0:
                logging.info(
                    f"Skipping House and Senate URLS: {AGENCY_DATA['AGENCY_ID']} {AGENCY_DATA['URL_FIELD']}"
                )
            continue

        # skipping all regular sites for senate or house pulls
        if (
            (not re.search(".senate.gov", AGENCY_DATA["URL_FIELD"]))
            and (not re.search(".house.gov", AGENCY_DATA["URL_FIELD"]))
        ) and program_state["pull_house_and_senate"]:
            logging.info(
                f"Skipping Non Senate/House URLS because -S is passed: {AGENCY_DATA['AGENCY_ID']} {AGENCY_DATA['URL_FIELD']}"
            )
            continue

        if (program_state["pull_house_and_senate"]) and not program_state["test_run"]:
            PROGRAM_SLEEP = 20

            if len(program_state["specific_id"]) == 0:
                logging.info(f"*** {PROGRAM_SLEEP} SECOND PROGRAM DELAY ***")
                time.sleep(PROGRAM_SLEEP)

        # getting uname
        db_data["uname"] = helpers.get_uname(AGENCY_DATA, unames)
        if db_data["uname"] is None:
            continue

        # updating the number of urls processed
        globals.url_count += 1

        # Gathers the source code from landing page
        webpage_html = web_requests.get_website(
            AGENCY_DATA["FULL_URL"], driver, AGENCY_DATA
        ) or web_requests.cloudscrape_website(AGENCY_DATA["FULL_URL"], AGENCY_DATA)
        if webpage_html is None:
            logging.error(f"article_html is None")
            globals.landing_page_html_is_none.append(
                f"{AGENCY_DATA['AGENCY_ID']}: {AGENCY_DATA['FULL_URL']}"
            )
            continue

        # parsing through article containers
        article_html = container_scraper.get_containers(
            AGENCY_DATA["ARTICLE_CONTAINERS"], webpage_html
        )

        if article_html is None or len(article_html) == 0:
            logging.error("landing page getting containers html is none")
            globals.landing_page_containers_html_is_none.append(
                f"{AGENCY_DATA['AGENCY_ID']}: {AGENCY_DATA['FULL_URL']}"
            )
            continue
        # dictionary to store article contents
        article_contents: dict | None = {}

        # checking to gather one article at a time
        if single_gather:

            # keeps track of the amount of invalid dates a website has
            invalid_counter = 0

            # gathering links from landing page
            for article in article_html:

                if invalid_counter > globals.invalid_dates:
                    break

                # gathering contents for one article
                article_contents = gather_article.gather_contents(
                    AGENCY_DATA, article, driver
                )
                if article_contents is None:
                    continue

                # incrementing the invalid counter when date isn't recent
                if article_contents == "INVALID":
                    invalid_counter += 1
                    continue

                # transferring data to db
                storage.db_insert(
                    db_data,
                    article_contents,
                )
        else:
            # gathering contents for all articles and storing data
            article_contents = gather_all_articles.gather_contents(
                AGENCY_DATA, article_html, db_data, driver  # type: ignore
            )
            if article_contents is None:
                continue


# closing web driver at the end of pull
driver.quit()  # type: ignore

# logs scrape errors on test runs
if program_state["test_run"]:
    logging.info("Scrape errors found during run:")
    logging.info(globals.element_not_found)

logging.info("End of file message")
end = datetime.now()
elapsed = end - start
# removing the miliseconds part to make for cleaner logs
start_time = str(start).split(".")[0]
end_time = str(end).split(".")[0]
elapsed_time = str(elapsed).split(".")[0]

summary_msg = f"""

Load Version 2.1.0 02/04/2025
       Docs Loaded: {len(globals.successfully_added_doc)}
       URLS processed: {globals.url_count}
       DUPS skipped: {len(globals.duplicate_docs)}
       No Ledes found: {len(globals.no_lead_found)}

Passed Parameters:
       Pull House and Senate: {program_state["pull_house_and_senate"]}
       Number of days back: {program_state["amount_of_days"]}
       Start Time: {start_time}
       End Time: {end_time}
       Elapsed Time: {elapsed_time}
       Character Minimum Amount: {globals.char_limit_to_skip}

Errors:"""
if len(globals.invalid_load_time) > 0:
    summary_msg = (
        summary_msg
        + "\n\tInvalid Load Times:\n\t\t"
        + "\n\t\t".join(map(str, globals.invalid_load_time))
    )

if len(globals.no_uname_found) > 0:
    summary_msg = (
        summary_msg
        + "\n\tNo UNAME found:\n\t\t"
        + "\n\t\t".join(map(str, globals.no_uname_found))
    )

if len(globals.no_lead_found) > 0:
    summary_msg = (
        summary_msg
        + "\n\tNo Lede Found:\n\t\t"
        + "\n\t\t".join(map(str, globals.no_lead_found))
    )

if len(globals.filename_creation_error) > 0:
    summary_msg = (
        summary_msg
        + "\n\tFilename Creation Error:\n\t\t"
        + "\n\t\t".join(map(str, globals.filename_creation_error))
    )

if len(globals.filename_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tFilename Is None\n\t\t"
        + "\n\t\t".join(map(str, globals.filename_is_none))
    )

if len(globals.article_link_href_typeerror_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tArticle Link href failed to grab:\n\t\t"
        + "\n\t\t".join(map(str, globals.article_link_href_typeerror_none))
    )

if len(globals.article_description_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tArticle Description is None:\n\t\t"
        + "\n\t\t".join(map(str, globals.article_description_is_none))
    )

if len(globals.article_skipped_keyword_found) > 0:
    summary_msg = (
        summary_msg
        + "\n\tArticle Skipped Due to Keyword:\n\t\t"
        + "\n\t\t".join(map(str, globals.article_skipped_keyword_found))
    )

if len(globals.landing_page_html_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tLanding Page HTML is None:\n\t\t"
        + "\n\t\t".join(map(str, globals.landing_page_html_is_none))
    )

if len(globals.landing_page_containers_html_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tLanding Page Containers HTML is None:\n\t\t"
        + "\n\t\t".join(map(str, globals.landing_page_containers_html_is_none))
    )

if len(globals.unequal_titles_dates_links_counts) > 0:
    summary_msg = (
        summary_msg
        + "\n\tLanding Page Counts for titles,dates,links do not equal:\n\t\t"
        + "\n\t\t".join(map(str, globals.unequal_titles_dates_links_counts))
    )

if len(globals.date_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tDate Found NoneType:\n\t\t"
        + "\n\t\t".join(map(str, globals.date_is_none))
    )

if len(globals.title_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tTitle Found NoneType:\n\t\t"
        + "\n\t\t".join(map(str, globals.title_is_none))
    )

if len(globals.link_is_none) > 0:
    summary_msg = (
        summary_msg
        + "\n\tLink Found NoneType:\n\t\t"
        + "\n\t\t".join(map(str, globals.link_is_none))
    )


if len(globals.cloud_scrapper_error) > 0:
    summary_msg = (
        summary_msg
        + "\n\tCloud Scrapper Failed to Resolve:\n\t\t"
        + "\n\t\t".join(map(str, globals.cloud_scrapper_error))
    )

if len(globals.csv_line_error) > 0:
    summary_msg = (
        summary_msg
        + "\n\tCSV Line has improper setup:\n\t\t"
        + "\n\t\t".join(map(str, globals.csv_line_error))
    )
# wished i could do this all in an f string but it is what it is

# DDDD   OOO   CCC  SSS
# D   D O   O C    S
# D   D O   O C     SSS
# D   D O   O C        S
# DDDD   OOO   CCC  SSS

summary_msg = summary_msg + "\nDocs:"

if len(globals.successfully_added_doc) > 0:
    summary_msg = (
        summary_msg
        + "\n\tLoaded:\n\t\t"
        + "\n\t\t".join(map(str, globals.successfully_added_doc))
    )

if len(globals.duplicate_docs) > 0:
    summary_msg = (
        summary_msg
        + "\n\tDuplicates:\n\t\t"
        + "\n\t\t".join(map(str, globals.duplicate_docs))
    )

if len(globals.article_description_too_short) > 0:
    summary_msg = (
        summary_msg
        + "\n\tArticle Description Too Short:\n\t\t"
        + "\n\t\t".join(map(str, globals.article_description_too_short))
    )


logging.info(summary_msg)
empty_msg = ""
if program_state["pull_house_and_senate"]:
    empty_msg = " House and Senate"

if program_state["production_run"]:
    my_mail(
        "kmeek@targetednews.com",
        "kmeek@targetednews.com",
        "New Scrape Project"
        + empty_msg
        + " PULL :) "
        + start.strftime("%Y-%m-%d %H:%M:%S"),
        summary_msg,
        "",
        "struckvail@aol.com;camhakenson@gmail.com,carterstruck02@gmail.com,marlynvitin@yahoo.com",
    )
    pass
