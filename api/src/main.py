
# Standard imports
import os 
import logging 

# Flask imports
from flask import Flask, request, abort
from gevent.pywsgi import WSGIServer
from configparser import ConfigParser

# Blueprints
from blueprints import data_bp

# Object and util imports
from classes import ResDBConnector 
from utils import setup_logger
from hooks import create_app


# ---- CONFIG ---- # 

# Fix rel path setup
SRC_DIR = os.path.dirname(os.path.abspath(__file__))    # Absolute path to src/
BASE_DIR = os.path.dirname(SRC_DIR)                     # Absolute path to main/

# Init and read config
config:ConfigParser = ConfigParser() 
config.read(os.path.join(BASE_DIR, 'config.conf'))

# Build paths
LOGS_DIR:str = os.path.join(BASE_DIR, config["paths"]["LOGS_DIR"])   # Path to the directory containing log files
DATA_DIR:str = os.path.join(BASE_DIR, config["paths"]["DATA_DIR"])   # Path to the directory containing all the data and database file

# Create paths from bases in config 
FLASK_LOG_FILE:str = os.path.join(LOGS_DIR, 'flask.log')  # Path to the output log file for the flask app
DB_FILE:str = config['paths']['DATABASE_FILEPATH']               # Path to the database file 

# Extract other vars from config for easier reference
CORS_ORIGIN:str = config['api']['CORS_ORIGIN']
RESET_LOGS:bool = config.getboolean('api', 'RESET_LOGS')


# ---- SETUP/INIT ---- # 

# Reset the logs dir if configured 
# NOTE: reset logs before init logger so that the log file is not locked
if RESET_LOGS: 
    for filename in os.listdir(LOGS_DIR): 
        if filename.endswith('.log'): os.remove(os.path.join(LOGS_DIR, filename))

# Setup the logger 
logger:logging.Logger = setup_logger(FLASK_LOG_FILE, config['logging']['FLASK_LOGGER_NAME'])

# Log if we reset the logs or not 
if RESET_LOGS: logger.debug('Reset all API logs.')
else: logger.debug('Keeping previous API logs.')

# Init the flask app
app:Flask = create_app(logger, CORS_ORIGIN) 

# Add DB connector to app for persistent access across blueprints
app.db_connector = ResDBConnector(DB_FILE)


# ---- REGISTER BLUEPRINTS ---- #
logger.info(f'Registering endpoints')
app.register_blueprint(data_bp)


# ---- DONE ---- # 
logger.debug('Flask app running!')
print(f'\033[92mFlask app running.\033[0m')


# ---- RUN ---- #
if __name__ == '__main__':
    try: 
        http_server = WSGIServer(('0.0.0.0', config.getint('api', 'BACKEND_PORT')), app)
        http_server.serve_forever()
    except Exception as e: 
        logger.critical('Flask app failed to start.', e, exc_info=True)