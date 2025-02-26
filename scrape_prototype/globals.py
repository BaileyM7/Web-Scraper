# used for lede formatting
month = [
    "zero",
    "Jan.",
    "Feb.",
    "March",
    "April",
    "May",
    "June",
    "July",
    "Aug.",
    "Sept.",
    "Oct.",
    "Nov.",
    "Dec.",
]
# trying to avoid specific sites keyword skips but using some here as just a global check
# searches through description
keyword_skips = ["PRNewswire", "Desarrollo Economico", "Asociacion Americana", "Gouvernement"]

# number of invalid dates until web skip
invalid_dates: int = 4

# id chosen to be tested
single_id: int = 0


# number of urls processed
url_count: int = 0

# Possible error that fails to access website
failed_access: list[str] = []

# Failed access for 403 error only
failed_access_403: list[str] = []


# list for rejected docs that failed to gather data
# valid docs there but just not gathered
rejected_docs: list[str] = []

# error for when no links are gathered
no_links: list[str] = []

# list for when checkign titles and date size
no_titles: list[str] = []

# carter lists

# succesffully added docs x
successfully_added_doc: list[str] = []

# number of duplicates in the given pull x
duplicate_docs: list[str] = []

# x means its added to the main
# errors
# skipping with no lede x
no_uname_found: list[str] = []

# skipping with no lede x
no_lead_found: list[str] = []

# unable to create filename x
filename_creation_error: list[str] = []

# getting filename returns none  x
filename_is_none: list[str] = []

# invalid load time field x
invalid_load_time: list[str] = []

# list to print out element scrape errors
element_not_found: list[str] = []

# landing page giving a none value x
# when trying to find the href of the landing page
article_link_href_typeerror_none: list[str] = []

# description is none or len is none x
article_description_is_none: list[str] = []

# articles that were skipped due to a key word
# log them so we know x
article_skipped_keyword_found: list[str] = []

# certain character limit set for size x
char_limit_to_skip: int = 100
article_description_too_short: list[str] = []

# when retriving initiall html this is the list of erros
landing_page_html_is_none: list[str] = []

# tried to get containers for landing page
landing_page_containers_html_is_none: list[str] = []

# checks for links==dates==titles amounts
unequal_titles_dates_links_counts: list[str] = []

# cloud scraper errors
cloud_scrapper_error: list[str] = []

# none objects for titles, dates, links
date_is_none: list[str] = []

title_is_none: list[str] = []

link_is_none: list[str] = []

# could be list of int but just easier
csv_line_error: list[str] = []
