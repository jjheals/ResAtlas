from flask import Flask, request, abort
from flask_compress import Compress
from flask_cors import CORS
import logging 


def create_app(logger:logging.Logger, cors_origin:str|list[str], allow_headers:list[str]=['Content-Type'], register_test_endpoint:bool=True) -> Flask: 

    # Init the app 
    logger.info('Initializing flask app.')

    app = Flask(__name__)
    compress = Compress()
    compress.init_app(app)

    # Configure CORS 
    logger.info('Configuring CORS.')
    CORS(
        app, 
        origins=cors_origin,
        allow_headers=allow_headers
    )  

    # Register the before/after request hooks
    register_request_hooks(app, logger, cors_origin)

    # Register a testing endpoint 
    if register_test_endpoint: 
        @app.route('/hello', methods=['GET'])
        def hello(): 
            return "I'm alive!"

    # Return the app
    return app


def register_request_hooks(app:Flask, logger:logging.Logger, cors_origin:str|list[str]):

    # Define the headers for the response that are the same no matter what the response is 
    response_headers:dict[str, str] = {
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    # Logging and init db cxn before requests
    @app.before_request
    def before_request():

        # Log incomming request
        try: 
            logger.info(f"INCOMING request: METHOD = {request.method}, PATH = {request.path}")
            logger.debug(f'Headers: {dict(request.headers)}')

            # Restrict to localhost connections
            if request.remote_addr not in ("127.0.0.1", "::1"):
                logger.warning(f"Rejected request from {request.remote_addr}")
                abort(403, description="Access denied: only localhost connections are allowed.")

            # Log body or params based on req type
            match(request.method): 
                case 'POST': 
                    logger.debug(f'Request body: {request.get_json()}')
                case 'GET': 
                    logger.debug(f'Request args: {request.args}')
                case _: 
                    pass
        except Exception as e: 
            logger.error('Error from incoming connection.', exc_info=e)


    # Logging for after requests and adding CORs headers
    @app.after_request
    def after_request(response):

        # Add response headers 
        for k,v in response_headers.items(): response.headers[k] = v
        
        # Log and return 
        logger.info(f'OUTGOING response: {request.remote_addr} {request.method} {request.path} | HEADERS: {dict(response.headers)}')
        return response 
