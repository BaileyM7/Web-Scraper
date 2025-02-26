from scrapers.content_scraper import scrape_content
import bs4.element
import html2text
import logging
import re
import globals

"""
* Description Formatting

CSV configuration: find/find_all|class/id/elem...|container_name~(repeat for another element removed)
"""


# desc_formatter formats the scraped description
def desc_formatter(
    article_description: bs4.element.Tag | list[bs4.element.Tag],
    AGENCY_DATA: dict,
):

    if AGENCY_DATA["DESC_REMOVE_DATA"] != "":
        desc_data_split: list[str] = AGENCY_DATA["DESC_REMOVE_DATA"].split("~")

        # removing elements as specified in csv
        for data in desc_data_split:
            remove_element(article_description, data, AGENCY_DATA["AGENCY_ID"])

    body = html2text.HTML2Text()
    body.ignore_links = True
    body.ignore_images = True
    body.ignore_tables = True
    body.ignore_emphasis = True
    body.ignore_mailto_links = True
    body.body_width = 0

    if isinstance(article_description, bs4.ResultSet) or isinstance(
        article_description, list
    ):
        formatted_body = ""
        for p in article_description:
            formatted_body += body.handle(str(p.prettify())) + "\n"
    else:
        formatted_body = body.handle(str(article_description.prettify()))

    return formatted_body


# remove_element helper function for desc_formatter
# @typechecked
def remove_element(
    article_description: bs4.element.Tag | list, DESC_REMOVE_DATA: str, AGENCY_ID: str
):

    find_all = True if "find_all" in DESC_REMOVE_DATA else False

    # Will require a loop to remove data if the description is of type list
    if isinstance(article_description, list):

        for para in article_description:

            elements_to_remove = scrape_content(
                DESC_REMOVE_DATA, para, AGENCY_ID, "DESC REMOVAL"
            )
            if find_all:
                if elements_to_remove is not None:
                    for element in elements_to_remove:
                        element.decompose()
            else:
                if elements_to_remove is not None:
                    elements_to_remove.decompose()

    else:
        elements_to_remove = scrape_content(
            DESC_REMOVE_DATA, article_description, AGENCY_ID, "DESC REMOVAL"
        )
        if find_all:
            if elements_to_remove is not None:
                for element in elements_to_remove:
                    element.decompose()
        else:
            if elements_to_remove is not None:
                elements_to_remove.decompose()


# TODO rough draft for default replacing
def replace_defaults(desc):

    # regex to remove from every article
    re_strings = [
        r"#\s?#\s?#",
        r"\s*Image\s*",
        r"FOR IMMEDIATE RELEASE",
        # r"[\[,\(]?[wW][aA][sS][hH][iI][nN][gG][tT][oO][nN]\.?\s?[,,-]*\s?[dD]?\.?[cC]?\s*\.?[\],\)]?\s?[-,:][-]*\s?[\.,\s]?[Uu]\.?[Ss]\.?[.,\s]?",
        r"[wW][aA][sS][hH][iI][nN][gG][tT][oO][nN],?\s?[dD]\.?[cC]\s*\.?\s*--*\s?"
        r"\s?[dD]\.?[cC]\s*\.?\s*--*\s*",
        r"##\s\s",
        r">\s",
        r"\s~~~~\s",
    ]

    for str in re_strings:
        desc = re.sub(str, "", desc)

    # checks for a date to be found within the description and removes it
    # catches a stop iteration if there is no date
    # try:
    #     extracted_date = next(datefinder.find_dates(desc, True))[1]
    #     desc = re.sub(f"(\()?{extracted_date}(\))?\s?-*\s?", "", desc, 1)
    # except StopIteration:
    #     pass

    return desc


# DEBUG: first implementation for title formatting
# currently only handles the removal of one element
# cannot call 'find_all' to remove
def format_title(title: str, format_data: str, agency_id: str) -> str:

    if isinstance(title, list):
        title = title[0]
    
    # getting none type on a title for a site with an extra container with a next page link
    # stopping error handle error outside of the function in gather_all_articles
    if title is None:
        return None

    if "|" in format_data:
        data = format_data.split("|")
        attribute = {data[1]: data[2]}
        if data[0] == "find":
            if data[1] == "elem":
                element_to_remove = title.find(data[2])
                title = title.text
                title.replace(element_to_remove.text.strip(), "")
            else:
                element_to_remove = title.find(attrs=attribute)
                title = title.text
                title.replace(element_to_remove.text.strip(), "")
        else:
            logging.error(
                "Title formatting error: can only call 'find' to remove element from title"
            )
            title = title.text
    else:
        title = title.text.replace(format_data, "")

    return title.strip()
