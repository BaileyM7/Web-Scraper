from typeguard import typechecked
from datetime import datetime
from globals import month
import logging


# format_lede inserts data into the lede where there are placeholders
@typechecked
def format_lede(lede: str, article_contents: dict) -> str:

    # creating a date format for the lede
    lede_date = datetime.strptime(article_contents["date"], "%Y-%m-%d")
    lede_month = month[lede_date.month]
    lede_day = lede_date.day

    logging.info(f"LEDE: [{lede}] month: [{lede_month}] day: [{lede_day}]")

    # replacing lede placeholder with date information
    lede = lede.replace("DATE", f"{lede_month} {lede_day}")

    return lede
