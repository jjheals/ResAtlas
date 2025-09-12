

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