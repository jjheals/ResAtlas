# test_check_table_available.py
import sqlite3 as sql
import pytest
from datetime import datetime, timedelta

# --- Minimal shim so we don't depend on your base DatabaseConnector in tests ---
class HelperResDBConnector:
    """
    A lightweight test double that only includes the bits we need:
    - .cxn                -> SQLite connection
    - ._ensure_cxn()      -> no-op guard
    - .log_error(...)     -> no-op logger
    - .check_table_available(...) -> the method under test (copied verbatim)
    """
    __test__ = False  # ensure pytest doesn't try to collect this as a test class

    def __init__(self, cxn: sql.Connection):
        self.cxn = cxn

    def _ensure_cxn(self):
        if self.cxn is None:
            raise RuntimeError("No connection")

    def log_error(self, *args, **kwargs):
        pass  # silence logs in tests
    
    # NOTE: same implementation as ResDBConnector class
    def check_table_available(self, table_number: int, datetime: str, spacing: float) -> bool:
        
        self._ensure_cxn()
        cursor: sql.Cursor = self.cxn.cursor()
        try:
            if spacing <= 0:
                cursor.execute(
                    """
                        SELECT 1
                        FROM ReservationAtTable
                        WHERE table_number = ?
                        AND reservation_datetime = ?
                        LIMIT 1
                    """,
                    (table_number, datetime),
                )
            else:
                cursor.execute(
                    """
                        SELECT 1
                        FROM ReservationAtTable
                        WHERE table_number = ?
                        AND ABS(julianday(reservation_datetime) - julianday(?)) * 24 < ?
                        LIMIT 1
                    """,
                    (table_number, datetime, float(spacing)),
                )
            return cursor.fetchone() is None
        except Exception as e:
            self.log_error("check_table_available()", e)
            return False
        finally:
            cursor.close()


# ---------- Fixtures: database & test helper inserts ----------

@pytest.fixture
def cxn():
    conn = sql.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    # Minimal schemas to satisfy FKs
    # NOTE: 
    # - Schema slightly different than actual schema to simplify testing
    # - Reservation: 
    #   - In test: date_created DOES NOT have "not null" constraint - actual schema does
    #   - In test: num_people has DEFAULT 2 - actual schema is "not null" 
    # - _Table: 
    #   - Minimal to just table number
    # - Customer: 
    #   - In test: no CHECK constraints - actual schema has checks on phone number and names/phone combo
    
    conn.executescript(
        """
        CREATE TABLE Customer (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name  TEXT,
            phone_number TEXT,
            email TEXT
        );


        CREATE TABLE Reservation(
            reservation_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            num_people INTEGER DEFAULT 2,
            reservation_datetime TEXT NOT NULL,
            date_created TEXT,
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


        CREATE TABLE _Table (
            table_number INTEGER PRIMARY KEY
        );

        
        CREATE TABLE ReservationAtTable(
            reservation_id INTEGER NOT NULL,
            reservation_datetime TEXT NOT NULL,
            table_number INTEGER NOT NULL,
            PRIMARY KEY (reservation_id, reservation_datetime, table_number),
            FOREIGN KEY (reservation_id, reservation_datetime)
                REFERENCES Reservation(reservation_id, reservation_datetime),
            FOREIGN KEY (table_number) REFERENCES _Table(table_number)
        );
        """
    )

    # Seed a couple of tables as inventory
    conn.executemany("INSERT INTO _Table(table_number) VALUES (?)", [(1,), (2,), (3,)])

    yield conn
    conn.close()


@pytest.fixture
def svc(cxn):
    return HelperResDBConnector(cxn)


def _mk_res(cxn, res_id: int, table_number: int, when_str: str, customer_id: int = 1):
    """Helper: insert a Reservation row + link it to a table in ReservationAtTable (satisfying FKs)."""
    # Ensure a customer exists
    cxn.execute(
        "INSERT OR IGNORE INTO Customer(customer_id, first_name, last_name, phone_number, email) "
        "VALUES (?, 'A','B','000','')",
        (customer_id,),
    )
    # Insert reservation (note: composite PK requires both columns)
    cxn.execute(
        "INSERT INTO Reservation(reservation_id, customer_id, reservation_datetime) VALUES (?, ?, ?)",
        (res_id, customer_id, when_str),
    )
    # Attach to table
    cxn.execute(
        "INSERT INTO ReservationAtTable(reservation_id, reservation_datetime, table_number) VALUES (?, ?, ?)",
        (res_id, when_str, table_number),
    )
    cxn.commit()


# ---------- Tests ----------

def test_available_when_no_reservations(svc, cxn):
    target = "2025-09-14 18:00:00"
    assert svc.check_table_available(1, target, spacing=2.0) is True


def test_conflict_same_moment_spacing_zero(svc, cxn):
    target = "2025-09-14 18:00:00"
    _mk_res(cxn, res_id=101, table_number=1, when_str=target)
    # spacing <= 0 path uses equality check
    assert svc.check_table_available(1, target, spacing=0.0) is False
    assert svc.check_table_available(1, target, spacing=-1.0) is False


def test_conflict_same_moment_with_positive_spacing(svc, cxn):
    target = "2025-09-14 18:00:00"
    _mk_res(cxn, res_id=102, table_number=1, when_str=target)
    # any positive spacing should see this as a conflict
    assert svc.check_table_available(1, target, spacing=2.0) is False


def test_conflict_within_spacing_window(svc, cxn):
    base = datetime(2025, 9, 14, 18, 0, 0)
    existing = (base + timedelta(minutes=90)).strftime("%Y-%m-%d %H:%M:%S")  # +1h30m
    target = base.strftime("%Y-%m-%d %H:%M:%S")
    _mk_res(cxn, res_id=103, table_number=1, when_str=existing)
    # spacing=2h => 1h30m < 2h -> conflict
    assert svc.check_table_available(1, target, spacing=2.0) is False


def test_no_conflict_outside_spacing_window(svc, cxn):
    base = datetime(2025, 9, 14, 18, 0, 0)
    existing = (base + timedelta(hours=2, minutes=1)).strftime("%Y-%m-%d %H:%M:%S")  # 2h1m away
    target = base.strftime("%Y-%m-%d %H:%M:%S")
    _mk_res(cxn, res_id=104, table_number=1, when_str=existing)
    assert svc.check_table_available(1, target, spacing=2.0) is True


def test_boundary_exactly_equals_spacing_is_allowed_with_strict_lt(svc, cxn):
    base = datetime(2025, 9, 14, 18, 0, 0)
    existing = (base + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")  # exactly 2h away
    target = base.strftime("%Y-%m-%d %H:%M:%S")
    _mk_res(cxn, res_id=105, table_number=1, when_str=existing)
    # Current SQL uses "< spacing", so exactly-equal should NOT conflict -> available True
    assert svc.check_table_available(1, target, spacing=2.0) is True


def test_same_time_different_table_is_available(svc, cxn):
    target = "2025-09-14 18:00:00"
    # Reservation on table 2 at the same time should not block table 1
    _mk_res(cxn, res_id=106, table_number=2, when_str=target)
    assert svc.check_table_available(1, target, spacing=2.0) is True


def test_handles_missing_table_gracefully_when_querying(svc, cxn):
    # There is no row in _Table for table 999, but check_table_available only reads ReservationAtTable,
    # so it should still return True (no conflicts).
    target = "2025-09-14 18:00:00"
    assert svc.check_table_available(999, target, spacing=2.0) is True
