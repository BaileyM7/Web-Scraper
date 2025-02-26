import scrapers.container_scraper as container_scraper
import scrapers.content_scraper as content_scraper
import logging
import bs4.element


# gather_description handles the description gathering for the different gather branches
def gather_description(AGENCY_DATA: dict, article_webpage_html: bs4.element.Tag):

    alternate_desc_data = AGENCY_DATA["DESCRIPTION_DATA"].split("<>")

    for desc in alternate_desc_data:
        desc_split_data = desc.split("~")

        # making this expecting the max to be 2
        if len(desc_split_data) == 2:
            # finding a container for description
            article_webpage_html = container_scraper.get_containers(
                desc_split_data[0], article_webpage_html
            )
            desc = desc_split_data[1]
            if article_webpage_html == None:
                continue

        article_description = content_scraper.scrape_content(
            desc,
            article_webpage_html,
            AGENCY_DATA["AGENCY_ID"],
            "DESC",
        )
        if article_description != None:
            break

    return article_description
