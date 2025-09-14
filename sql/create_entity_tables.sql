
-- ENABLE FOREIGN KEY CONSTRAINTS 
PRAGMA foreign_keys = ON;


/** Customer(customer_id, first_name, last_name, phone_number, email)
 * - Each customer can have many or zero reservations
 * - Each customer has exactly one phone number 
 * - Two or more customers can have the same phone number
 * - Two or more customers with the same phone number cannot have the same first and last name
 */
CREATE TABLE Customer(
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    email TEXT DEFAULT NULL,
    
    -- Enforce phone number format 
    CHECK(
        LENGTH(phone_number) = 14   -- Exactly 14 chars
        AND phone_number GLOB '([0-9][0-9][0-9]) [0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'  -- "(000) 000-0000" format 
    ),

    -- Enforce unique (first_name, last_name, phone_number) 
    UNIQUE (first_name, last_name, phone_number)
);


/** Reservation(reservation_id, customer_id, table_set_id, reservation_datetime, date_created, notes)
 * - Each customer can create one or more reservations
 * - Each reservation is owned by exactly one customer
 * - Each reservation will be assigned to exactly one TableSet
 * - Each reservation can have a number of highchairs assigned, which are INCLUDED in the num_people count
 */
CREATE TABLE Reservation(
    reservation_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    num_people INTEGER NOT NULL,
    reservation_datetime TEXT NOT NULL,
    date_created TEXT NOT NULL,
    num_highchairs INTEGER DEFAULT 0,
    notes TEXT DEFAULT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),

    -- Enforce res_datetime and date_created are ISO format (YYYY-MM-DD HH:MM:SS)
    CHECK(
        reservation_datetime GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'
        AND date_created GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'
    )   

    -- Enforce that a customer can only have one reservation at a given time
    UNIQUE (customer_id, reservation_datetime),

    -- Make FK for ReservationAtTable targetable 
    UNIQUE (reservation_id, reservation_datetime)
);


/** Table(table_number, default_chairs, max_chairs, **) 
 * - Each table has a unique table_number 
 * - Each table is assigned a default number of chairs, which is the number of chairs automatically set for that table
 * - Each table is assigned a max number of chairs, which is the maximum number of chairs that will fit at that table 
 * - The top left/bottom left/top right/bottom right corners of the table's geometry should be saved
 */
CREATE TABLE _Table(
    table_number INTEGER PRIMARY KEY,      
    default_chairs INTEGER NOT NULL,    -- Number of chairs that this table is set for
    max_chairs INTEGER NOT NULL,        -- Maximum number of chairs that will fit at this table

    -- Top left corner (tl_x, tl_y)
    tl_x REAL NOT NULL,   
    tl_y REAL NOT NULL,    

    -- Top right corner (tr_x, tr_y)
    tr_x REAL NOT NULL,
    tr_y REAL NOT NULL,

    -- Bottom left corner (bl_x, bl_y)
    bl_x REAL NOT NULL,
    bl_y REAL NOT NULL,

    -- Bottom right corner (br_x, br_y)
    br_x REAL NOT NULL,
    br_y REAL NOT NULL,

    -- Enforce geometry
    CHECK(
        tl_x < tr_x        -- Top left X < top right X
        AND bl_x < br_y    -- Bottom left X < bottom right X
        AND tl_y > bl_y    -- Top left Y > bottom left Y
        AND tr_y > br_y    -- Top right Y > bottom right Y
    )  
);


/** Layout(layout_id, layout_common_name) 
 ** Section(section_id, section_common_name)
 * - A Layout is comprised of many Sections, where each Section can be part of many Layouts
 * - Each Section contains many Tables, and each Table can be in many Sections
 * - Each Section should be assigned a "number", which is unique ONLY to that Layout
        - The section_id is GLOBALLY UNIQUE
        - The section_number is UNIQUE ONLY IN THE LAYOUT 
 * - Each Section can optionally be assigned a server, which holds only for that section in a specific layout
 */
CREATE TABLE Layout(
    layout_id INTEGER PRIMARY KEY,
    layout_common_name TEXT DEFAULT NULL
);

CREATE TABLE Section(
    section_id INTEGER PRIMARY KEY,
    section_common_name TEXT DEFAULT NULL
);
