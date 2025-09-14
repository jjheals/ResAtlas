
class InvalidTableNumberError(Exception): 
    def __init__(self, table_numbers:list[int]|None=None):
        
        # Base message string
        msg:str = f'Given one or more invalid table numbers'
        
        # Add table numbers to message if given
        if table_numbers is not None: 
            msg += f': {table_numbers}'
        else: msg += '.'

        # Init parent
        super.__init__(msg)
        self.message = msg


class ReservationNotFound(Exception):
    def __init__(self, info:dict|None=None):

        # Base msg string
        msg:str = 'The reservation could not be found'

        # Add info if given
        if info is not None: 
            msg += f'. Given info: {info}'
        else: 
            msg += '.'

        # Init parent 
        super.__init__(msg)
        self.message = msg


class OverlappingReservationsError(Exception):
    def __init__(self, time:str, table_number:int, spacing:int): 
        msg:str = f'There is already a reservation at table "{table_number}" within {spacing} hours of "{time}".'
        super.__init__(msg)
        self.message = msg
        

        