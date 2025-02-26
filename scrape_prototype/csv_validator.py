import csv
import sys
import logging

# csv_file = "./configs/scrape_test.csv"

# previously took in entire file now will take in one line and validate it 
# avoiding one line being bad and stopping the entire run
def csv_validate(data_field):
    # TODO Think of all different ways to fail csv
    # TODO currently has a few tests to pass
    try:
        # *** URL VALIDATION ***
        # checks for the correct number of url fields
        if len(data_field[1].split("|")) > 2:
            logging.error("CSV INVALID: Too many url pipes (MAX 2)")
            logging.info(f"You put: {data_field[1]}")
            return None
        # *** ARTICLE CONTAINER VALIDATION ***
        container_split = data_field[2].split("~")
        # cecking for the correct number of container fields
        if len(container_split) > 2:
            logging.error("CSV INVALID: Too many containers to find (MAX 2)")
            logging.info(f"You put: {data_field[2]}")
            return None
        # Nt allowing invalid calls on result sets
        if (
            container_split[0].split("|")[0] == "find_all"
            and len(container_split) == 2
        ):
            logging.error(
                "CSV INVALID: Cannot try to find nested container after 'find_all'"
            )
            logging.info(f"You put: {data_field[2]}")
            return None
        # ** LANDING PAGE VALIDATION ***
        if data_field[3] == "":
            logging.error("CSV INVALID: Landing Page field is blank")
            logging.info(f"You put: {data_field[3]}")
            return None
        # ** DESCRIPTION GATHER VALIDATION ***
        # dscription_split = data_field[8].split("<>")
        # fr data in description_split:
        #    split_data = data.split("~")
        #    # Making sure you don't call find_all before find
        #    if len(split_data) == 2 and "find_all" in split_data[0]:
        #        logging.error(
        #            "CSV INVALID: Cannot try to find nested container after 'find_all'"
        #        )
        #        logging.error(f"You put: {split_data[0]}")
        #        sys.exit(2)
        # ** STATUS VALIDATION ***
        if data_field[-1] == "":
            return None
    except:
        # if somehow nothing passes or something breaks then just return none 
        # fail the line
        return None        
    return 1
