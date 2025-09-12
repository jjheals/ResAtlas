import datetime as dt 
import pandas as pd 
import sqlite3 as sql 

from database_connectors import DatabaseConnector
from database_connectors.classes.database_type import DatabaseType

from utils import standardize_phone_number, standardize_date


class ResDBConnector(DatabaseConnector):


    def __init__(self, db_filepath:str): 
        super().__init__(
            DatabaseType.SQLITE,
            host=None,
            username=None,
            password=None,
            database=db_filepath, 
            log_file_path='logs/ResDBConnector.log'
        )


    # ---- Methods for checking existing entries ---- #

    def get_customer_id(self, first_name:str, last_name:str, phone_number:str) -> int|None: 
        """Returns the customer_id if an existing customer matches ALL the given info (first name, last name, AND phone number), or None if no match is found."""
        try:
            # Normalize inputs
            fn:str = first_name.strip()
            ln:str = last_name.strip()
            ph:str = standardize_phone_number(phone_number)

            rows:list[tuple]|None = self.execute_one(
                'SELECT customer_id '
                'FROM Customer '
                'WHERE first_name = ? COLLATE NOCASE '
                '  AND last_name = ? COLLATE NOCASE '
                '  AND phone_number = ?',
                params=(fn, ln, ph),
                fetch_results=True,     # Yes fetch results
                commit=False            # No commit needed
            )

            # Return based on result
            if rows:
                return int(rows[0][0])  # rows like [(customer_id,)]
            return None
        
        # Handle all exceptions as "no match"
        except Exception as e: 
            self.log_error('check_customer_exists()', e)
            return None


    def get_reservation_id(self, customer_id:int, reservation_datetime:str) -> int|None: 
        """Returns the reservation_id for the given customer_id and reservation_datetime, or None if no
        matches are found."""
        try:
            # Execute the query
            rows: list[tuple] | None = self.execute_one(
                "SELECT reservation_id FROM Reservation "
                "WHERE customer_id = ? AND reservation_datetime = ? "
                "LIMIT 1",
                params=(customer_id, reservation_datetime),
                fetch_results=True,
                commit=False   
            )

            # Return based on result
            if rows: return int(rows[0][0])  # Rows like [(123,)]
            else: return None

        # Handle exceptions as "not found"
        except Exception as e:
            self.log_error('get_reservation_id()', e)
            return None
        

    def check_customer_has_reservation(self, customer_id:int, reservation_datetime:str) -> bool: 
        """Returns True if the given customer has a reservation for the given datetime, False otherwise."""
        try:
            # Execute query
            rows: list[tuple] | None = self.execute_one(
                "SELECT 1 FROM Reservation "
                "WHERE customer_id = ? AND reservation_datetime = ? "
                "LIMIT 1",
                params=(customer_id, reservation_datetime),
                fetch_results=True,
                commit=False  
            )

            # Return based on results (True if any rows are returned)
            return bool(rows)
        
        # Handle exceptions as "not found"
        except Exception as e:
            self.log_error('reservation_exists()', e)
            return False
        

    # ---- Methods for creating new entries ---- # 

    def new_reservation(
        self,
        customer_fn:str, 
        customer_ln:str, 
        customer_phone:str, 
        num_people:int, 
        reservation_datetime:str,
        customer_email:str|None=None,
        date_created:str|None=None,
        table_set_id:int|None=None,
        num_highchairs:int|None=None,
        notes:str|None=None
    ) -> int: 
        """Creates a new entry in the [Reservation] table and returns the newly created ID
            - Kwargs are optional and will be omitted in the insert if not provided
            - The customer will be created if there is no customer with the matching info, otherwise the existing
            customer will be used.
        
            Raises: 
            - ValueError: if an invalid parameter is given or if a required parameter is missing
            - KeyError: if there is an error retrieving or inserting the customer's information
            - sql.IntegrityError: if the given customer already has a reservation for the given datetime
            - sql.DataError: if there is any error inserting the reservation 
        """
        self.log_debug('new_reservation()', f'Creating a new reservation for "{customer_fn} {customer_ln}" on "{reservation_datetime}"')

        # Validate input params
        try: 
            # Standardize inputs
            customer_fn = customer_fn.strip()
            customer_ln = customer_ln.strip()
            customer_phone = standardize_phone_number(customer_phone)
            reservation_datetime = standardize_date(reservation_datetime)
            
            if num_highchairs is None: num_highchairs = 0
            if customer_email is None: customer_email = ''
            if notes is None: notes = ''

            # NOTE: if date_created is invalid, default to today (now)
            try: 
                date_created = standardize_date(date_created)
            except ValueError: 
                date_created = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Check that others are the correct type and within appropriate bounds
            assert isinstance(num_people, int)
            
        # Exception means an input was invalid
        except Exception as e: 

            # Log the original error
            self.log_error('new_reservation()', e)

            # Log the ValueError (for invalid param)
            exception:ValueError = ValueError('Invalid parameter given to new_reservation().')
            self.log_error('new_reservation()', exception)

            # Raise the ValueError
            raise exception

        # Create the customer if they do not exist, or get the existing ID (and update email)
        self.log_debug('new_reservation()', f'Creating or updating customer information for "{customer_fn} {customer_ln}" (phone = "{customer_phone}")')
        customer_id:int|None = self.insert_update_customer(customer_fn, customer_ln, customer_phone, email=customer_email)

        # Check that an ID was found or that the insert was successful
        if customer_id is None: 
            
            # Create and log the exception
            exception:KeyError = KeyError('There was an error retrieving or inserting the info for the given customer.')
            self.log_error('new_reservation()', exception)

            # Raise the exception
            raise exception

        # If the customer DOES exist, check if they have a reservation for this datetime already
        else: 
            if self.check_customer_has_reservation(customer_id, reservation_datetime):

                # Log a clear warning message
                self.log_warning('new_reservation()', f'Customer (id = {customer_id}) already has a reservation for "{reservation_datetime}"')

                # Create and log an exception
                exc:Exception = sql.IntegrityError(f'Customer (id = {customer_id}) already has a reservation for "{reservation_datetime}"')
                self.log_error('new_reservation()', e)

                # Raise the exception
                raise exc
        
        # Create a new Reservation for this customer depending on the given params
        params_dict:dict = {
            'customer_id': customer_id,
            'reservation_datetime': reservation_datetime,
            'num_people': num_people,
            'num_highchairs': num_highchairs,
            'date_created': date_created,
            'notes': notes
        }   

        # Add other attributes if they are given
        if table_set_id is not None and isinstance(table_set_id, int): 
            params_dict['table_set_id'] = table_set_id

        # Insert the new row
        self.log_debug('new_reservation()', 'Creating new Reservation entry.')
        self.new_table_row(
            params_dict,
            'Reservation'
        )

        # Retrieve the ID of the newly inserted reservation
        res_id:int|None = self.get_reservation_id(customer_id, reservation_datetime)

        # NOTE: self.new_table_row() fails silently, so perform a manual check to see if the insert was successful
        # Check that insert was successful 
        if res_id is None: 
            
            # Create and log the error
            exc:Exception = sql.DataError(f'Failed to create new reservation for Customer (id = {customer_id}) at date time "{reservation_datetime}"')
            self.log_error('new_reservation()', exc)

            # Raise the error
            raise exc
        
        # Return the new reservation ID
        self.log_debug('new_reservation()', f'Successfully created Reservation (id = {res_id})')
        return res_id
    

    def insert_update_customer(self, first_name:str, last_name:str, phone_number:str|int, email:str='') -> int|None: 
        """If the given info does not already exist for a customer, then a new customer is created and the ID of the newly created customer
        is returned; if the given info does already exist, then the existing customer's (mutable) info is updated with the new info and the 
        existing customer ID is returned.
        
        NOTE: returns None if an error occurs.
        """

        # Normalize inputs
        first_name = first_name.strip()
        last_name = last_name.strip()
        phone_number = str(phone_number).strip()
        email = email.strip()

        # Check if the customer exists already
        existing_id:int|None = self.get_customer_id(first_name, last_name, phone_number)

        if existing_id is not None: 

            # Update the customer's mutable attributes (just email)
            if email: 
                self.execute_one(
                    'UPDATE Customer SET email = ? WHERE customer_id = ?', 
                    [email, existing_id]
                )

            # Return the existing ID
            return existing_id

        # If the customer doesn't exist, create an entry
        try: 

            # Insert the new row
            self.new_table_row(
                (first_name, last_name, phone_number, email),
                'Customer',
                cols=['first_name', 'last_name', 'phone_number', 'email']   # NOTE: omit customer_id col
            )

            # Get the newly inserted ID
            return self.get_customer_id(first_name, last_name, phone_number)

        # Handle all exceptions
        except Exception as e: 
            self.log_error('insert_update_customer()', e)
            return None
        

    # ---- Methods for retrieving filtered data ---- # 

    def get_reservations_for_date(self, date:dt.datetime) -> pd.DataFrame: 
        """Returns a DataFrame containing the subset of [Reservations] that are on the given date."""

        # Get the full [Reservation] table
        reservations_df:pd.DataFrame = self.table_as_df('Reservation')

        # Convert the "reservation_datetime" to dt.datetime type
        reservations_df['reservation_datetime'] = pd.to_datetime(reservations_df['reservation_datetime'])

        # Filter the df and return 
        return reservations_df[
            reservations_df['reservation_datetime'].dt.date == date.date()
        ]
    
