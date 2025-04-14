# db_insert.py
import mysql.connector
from mysql.connector import IntegrityError, DataError
from datetime import datetime
import logging
import yaml

def get_db_connection(yml_path="configs/db_config.yml"):
    with open(yml_path, "r") as yml_file:
        config = yaml.load(yml_file, Loader=yaml.FullLoader)
    return mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )

def insert_press_release(headline, date_str, body, a_id, filename, url, uname="openai"):
    """
    Insert a new press release entry with the URL as a standalone element (source_url).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO tns.press_release 
            (headline, content_date, body_txt, a_id, status, create_date, last_action, filename, 
             headline2, uname, source_url)
        VALUES 
            (%s, %s, %s, %s, %s, SYSDATE(), SYSDATE(), %s, %s, %s, %s)
        """

        cursor.execute(query, (
            headline[:254],  # Truncate to stay within column limit if needed
            date_str,
            body,
            a_id,
            "D",  # status
            filename,
            "",   # headline2
            uname,
            url   # <--- New field for URL
        ))

        conn.commit()
        logging.info(f"Inserted: {headline[:50]}...")
    except IntegrityError as err:
        logging.error(f"Duplicate entry: {err}")
    except DataError as err:
        logging.error(f"Data error: {err}")
    except Exception as err:
        logging.error(f"Database error: {err}")
    finally:
        if conn:
            conn.close()
