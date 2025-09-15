
-- ENABLE FOREIGN KEY CONSTRAINTS 
PRAGMA foreign_keys = ON;


/** ReservationAtTable(reservation_id, reservation_datetime, table_number)
 * - Reservation [MTM] Table
 * - Each Reservation can be assigned to zero, one, or many tables
 * - Only one reservation can be assigned to each table at a given time
 * - Enforced at code level: reservations can only be scheduled [X] hours apart
 */
CREATE TABLE ReservationAtTable(
    reservation_id INTEGER NOT NULL,
    reservation_datetime TEXT NOT NULL,
    table_number INTEGER NOT NULL,
    PRIMARY KEY (reservation_id, reservation_datetime, table_number),
    FOREIGN KEY (reservation_id, reservation_datetime) REFERENCES Reservation(reservation_id, reservation_datetime),
    FOREIGN KEY (table_number) REFERENCES _Table(table_number)
);



/** SectionInLayout(section_id, layout_id, section_number, server_name)
 * - Section (MTM) Layout
 * - Each section can be added to zero, one, or many layouts
 * - For each layout that it is added to, a section is assigned a section_number, which identifies that section in that layout
 * - For each layout that it is added to, a section can also optionally be assigned a server, which is unique only to that layout and may frequently change
 */
CREATE TABLE SectionInLayout(
    section_id INTEGER NOT NULL,
    layout_id INTEGER NOT NULL, 
    section_number INTEGER NOT NULL,                            -- section_number is only unique to a specific Layout
    server_name TEXT DEFAULT NULL,                              -- Optionally assign a server (for just this layout)
    PRIMARY KEY (section_id, layout_id),
    UNIQUE (layout_id, section_number),                         -- Required for FK of TableInSection and TableSetInSection
    FOREIGN KEY (section_id) REFERENCES Section(section_id),
    FOREIGN KEY (layout_id) REFERENCES Layout(layout_id)
);


/** TableInSection(table_number, layout_id, section_number)
 * - Table (MTO) Section
 * - Each Table can be assigned to many sections, but each section can only contain one or zero of each table
 * - Each Table can only be assigned to a single Section within a given Layout
 */
CREATE TABLE TableInSection(
    table_number INTEGER NOT NULL,
    layout_id INTEGER NOT NULL,
    section_number INTEGER NOT NULL,
    PRIMARY KEY (table_number, layout_id, section_number),
    FOREIGN KEY (table_number) REFERENCES _Table(table_number),
    FOREIGN KEY (layout_id, section_number) REFERENCES SectionInLayout(layout_id, section_number)
);
