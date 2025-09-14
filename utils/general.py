import logging 
import os 


def standardize_phone_number(phone_number:str|int) -> str: 
    """Takes in a phone number (as str or an int) and returns the number in (000) 000-0000 format; raises 
    ValueError if the given phone number is invalid."""
    import re 

    # Convert to string and strip non-digits
    digits:str = re.sub(r"\D", "", str(phone_number))
    
    # Handle 10-digit numbers
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    
    # Handle 11-digit numbers starting with "1" (common US country code)
    if len(digits) == 11 and digits.startswith("1"):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    
    # If format is wrong, raise error
    raise ValueError(f"Invalid phone number: {phone_number}")


def standardize_date(date_str:str) -> str: 
    """Converts the given date string to 'YYYY-MM-DD HH:MM:SS', or raises a ValueError if the given
    string is not a valid date string."""
    from pandas import to_datetime

    try: 
        return to_datetime(date_str, errors='raise').strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        raise ValueError(f'Invalid date string: {date_str}')
    

def setup_logger(log_file_path:str, logger_name:str, min_level:int=logging.DEBUG, log_format:str='%(asctime)s - %(levelname)s: %(message)s') -> logging.Logger:
    """Sets up a logger to save logs to the given filepath."""
    
    # Init a logger and set the lowest level to DEBUG (so all logs are captured)
    logger:logging.Logger = logging.getLogger(logger_name)
    logger.setLevel(min_level)
    
    # Prevent double logging if root logger is used
    logger.propagate = False  

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        
        # Create the output dir if it doesn't exist
        # NOTE: default path if log file path is None or empty string
        if log_file_path == None or not log_file_path: 
            log_file_path = './logger_output.log'

        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # Create a file handler
        file_handler:logging.FileHandler = logging.FileHandler(log_file_path, encoding='utf-8')
        logger.addHandler(file_handler)
        
        # Set the format for logs 
        formatter:logging.Formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        
    # Return the logger
    return logger