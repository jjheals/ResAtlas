import os 
import sqlite3 as sql
import pandas as pd 
from logging import Logger

from classes import ResDBConnector
from utils.general import setup_logger

# ---- CONFIG ---- # 

# Flags for running/testing
RESET_LOGS:bool = True      # Reset the "logs/" dir
RESET_DB:bool = True        # Reset the DB (drop and recreate all tables) 

# Standard paths
LOGS_DIR:str = 'logs/'                                      # Path to dir containing logs
DATABASE_FILE:str = 'data/test-database.db'                 # Path to the database SQLite file
CREATE_TABLES_SQL_SCRIPT:str = 'sql/create_tables.sql'      # SQL script for creating tables
DROP_TABLES_SQL_SCRIPT:str = 'sql/drop_tables.sql'          # SQL script for dropping existing tables

DUMMY_DATA_CSV:str = 'data/test-data/dummy-reservations.csv'    # CSV file containing dummy data for testing purposes
DB_AS_CSVS_DIR:str = 'data/test-data/db-as-csvs/'               # Dir to dump the DB as CSVs for inspecting and testing


# ---- SETUP ---- #

# Reset logs if configured
if RESET_LOGS: 
    for filename in os.listdir(LOGS_DIR): 
        os.remove(os.path.join(LOGS_DIR, filename))

# Init db connection
db_connector:ResDBConnector = ResDBConnector(DATABASE_FILE)

# Init a logger for this script
logger:Logger = setup_logger(
    os.path.join(LOGS_DIR, 'main-py.log'),
    'main-py-logger'
)


# Reset the DB if configured
if RESET_DB: 
    
    # Init a cursor
    cursor:sql.Cursor = db_connector.cxn.cursor()

    # Drop existing tables
    logger.debug('Dropping existing tables.')
    with open(DROP_TABLES_SQL_SCRIPT, 'r') as sql_script: 
        cursor.executescript(sql_script.read())
        db_connector.cxn.commit()

    # Create new tables
    logger.debug('Creating new tables.')
    with open(CREATE_TABLES_SQL_SCRIPT, 'r') as sql_script: 
        cursor:sql.Cursor = db_connector.cxn.cursor()
        cursor.executescript(sql_script.read())
        db_connector.cxn.commit()

    # Close cursor
    cursor.close()


# ---- ADDING/CHECKING DUMMY DATA ---- # 

# Load dummy data
res_data_df:pd.DataFrame = pd.read_csv(DUMMY_DATA_CSV)

# Create new entries for each of the reservations
logger.debug('Creating new Reservation entries')

for idx,row in res_data_df.iterrows(): 
    try: 
        db_connector.new_reservation(
            row['first_name'],
            row['last_name'],
            row['phone_number'],
            row['num_people'],
            row['reservation_datetime'],
            customer_email=row['email'],
            date_created=row['date_created'],
            num_highchairs=row['num_highchairs'],
            notes=row['notes']
        )
    except Exception as e: 
        logger.error(f'Error adding reservation (idx = {idx})', exc_info=e)

# Pull DB as CSVs to inspect
print(db_connector.get_all_table_names())

logger.debug(f'Pulling DB as CSVs to "{DB_AS_CSVS_DIR}"')
db_connector.db_as_csvs(DB_AS_CSVS_DIR)

# Done
logger.info('DONE.')
db_connector.cxn.close()
