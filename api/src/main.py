
# Standard imports
import os 
import logging 

# Flask imports
from flask import Flask, request, session, g
from gevent.pywsgi import WSGIServer
from flask_compress import Compress
import secrets 
from flask_cors import CORS  

# Blueprints
from .blueprints import data_bp

# Object and util imports
from .classes import ResDBConnector 
from .utils import setup_logger


# ---- CONFIG/SETUP ---- # 

# Vars
FLASK_LOG_FILE:str = '../logs/flask.log'
DB_FILE:str = '../data/database.db'

# Init a logger
logger:logging.Logger = setup_logger('../logs/flask.log', 'flask_logger')

# Init the flask app
logger.debug('Initializing flask app.')

app = Flask(__name__)
compress = Compress()
compress.init_app(app)

# Init CORS 
logger.debug('Configuring CORS.')
CORS(
    app, 
    origins='127.0.0.1',
    allow_headers=['Content-Type'],
    supports_credentials=True
)  

# Define the headers for the response that are the same no matter what the response is 
response_headers:dict[str, str] = {
    'Access-Control-Allow-Origin': '127.0.0.1',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Allow-Headers': 'Content-Type'
}

# Add DB connector to app for persistent access across blueprints
app.db_connector = ResDBConnector(DB_FILE)

# Logging and init db cxn before requests
@app.before_request
def before_request():

    # Log incomming request
    try: 
        logger.info(f"\n\033[92mINCOMING request: METHOD = {request.method}, PATH = {request.path}")
        logger.debug(f'Headers: {request.headers()}')
        
        # Log body or params based on req type
        match(request.method): 
            case 'POST': 
                logger.info(f'Request body: {request.get_json()}')
            case 'GET': 
                logger.info(f'Request args: {request.args}')
            case _: 
                pass
    except Exception as e: 
        logger.error('Error from incoming connection.', exc_info=e)

# Logging for after requests and adding CORs headers
@app.after_request
def after_request(response):
    #response.set_cookie('session', value=session['authenticated'], samesite='None', secure=False)
    for k,v in response_headers.items(): response.headers[k] = v
    
    print(f"\n\033[94mOUTGOING response: \n\n\t\033[0m{request.method} {request.path}\n\tAuthenticated: {session.get('authenticated')}\n")
    print(response.headers)

    return response 


# -- Endpoints -- #
print(f'\033[0m[{now()}] \033[94mRegistering endpoints\033[0m')

app.register_blueprint(homepage_bp)
app.register_blueprint(data_bp)
app.register_blueprint(authentication_bp)


# -- Debug print -- #
print(f'\033[0m[{now()}] \033[92mFlask app running.\033[0m')


# -- Run -- #
if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', config['backend-port']), app)
    http_server.serve_forever()