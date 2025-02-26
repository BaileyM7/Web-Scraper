from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from typeguard import typechecked
from datetime import datetime
from mysql.connector import MySQLConnection
import mysql.connector
import logging

# carter checked

# contains config variables for the program
# using a dict so data can be mutated and accessed from other files
program_state = {
    "amount_of_days": 1,
    "DEFAULT_LOAD_TIME": 0.5,
    "specific_id": "",
    "lede_filter": "%",
    "production_run": False,
    "test_run": False,
    "pull_house_and_senate": False,
}

# specifies the name of the csv file to use
CSV_FILE: str = "scrape_test.csv"


# selenium_setup starts the webdriver and enables headless driver and firefox
@typechecked
def selenium_config() -> webdriver:
    options: Options = Options()
    firefox_profile = webdriver.FirefoxProfile()

    # option to disable website caching and image loading to help with testing
    # trying to remove variability between pulls
    # firefox_profile.set_preference("permissions.default.image", 2)
    # firefox_profile.set_preference("browser.cache.disk.enable", False)
    # firefox_profile.set_preference("browser.cache.memory.enable", False)

    # options.add_argument(
    #    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    # )
    # options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.profile = firefox_profile
    driver: webdriver = webdriver.Firefox(options=options)
    return driver


# log_config will configure the logger for the main file
def log_config():
    logfile = "./logs/scrape_log.{}.log".format(
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
        filename=logfile,
        filemode="w",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)-12s: %(levelname)-8s %(message)s", datefmt="%H:%M.%S"
    )
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    # removes unwanted debugging from output
    logging.getLogger("mysql").setLevel(logging.CRITICAL)
    logging.getLogger("selenium").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("datefinder").setLevel(logging.CRITICAL)

    # * Uncomment code to view libraries using logger
    # loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    # for logger in loggers:
    #     print(
    #         f"Logger name: {logger.name}, Level: {logging.getLevelName(logger.level)}"
    #     )


# db_config initiates the sql connection based on user yml data
def db_config(yml_config: dict) -> MySQLConnection:
    database = mysql.connector.connect(
        host=yml_config["dbhost"],
        port=yml_config["dbport"],
        user=yml_config["dbuser"],
        passwd=yml_config["dbpasswd"],
        database="tns",
    )

    return database  # type: ignore


# query_config sets up the main query for execution
@typechecked
def query_config(yml_config: dict, lede_filter: str) -> str:
    query: str = (
        "SELECT a_id, filename, CONVERT({} using latin1), uname from agencies a join url_grp g on g.ug_id = a.ug_id where descrip like '{}';".format(
            yml_config["leadsfield"], lede_filter
        )
    )

    return query
