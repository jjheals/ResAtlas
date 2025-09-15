# test_update_reservation_tables.py
import pytest
import sqlite3 as sql

from classes.ResDBConnector import ResDBConnector
from classes.exceptions import *
from utils import *

@pytest.fixture
def connector(monkeypatch):
    """In-memory connector with logging stubbed out; DB calls will be monkeypatched per-test."""
    c = ResDBConnector(":memory:")

    # Silence logs but keep call recording if needed
    logged = {"errors": [], "warnings": [], "debug": []}

    def log_error(ctx, e):
        logged["errors"].append((ctx, e))

    def log_warning(ctx, msg):
        logged["warnings"].append((ctx, msg))

    def log_debug(ctx, msg):
        logged["debug"].append((ctx, msg))

    monkeypatch.setattr(c, "log_error", log_error, raising=False)
    monkeypatch.setattr(c, "log_warning", log_warning, raising=False)
    monkeypatch.setattr(c, "log_debug", log_debug, raising=False)
    c._logged = logged
    return c


def _stub_reservation_info(monkeypatch, connector, res_id=1, when="2025-09-14 18:30:00"):
    monkeypatch.setattr(
        connector,
        "get_reservation_info",
        lambda rid: {"reservation_id": rid, "reservation_datetime": when} if rid == res_id else None,
        raising=False,
    )
    return when


def test_raises_when_reservation_not_found(connector, monkeypatch):
    _stub_reservation_info(monkeypatch, connector, res_id=999)  # only id=999 exists

    # ask for a different id -> not found
    with pytest.raises(sql.DataError):
        connector.update_reservation_tables(reservation_id=1, table_numbers=[10])

    # sanity: logged an error
    assert connector._logged["errors"], "Expected an error to be logged"


def test_raises_on_invalid_table_numbers(connector, monkeypatch):
    _stub_reservation_info(monkeypatch, connector, res_id=1)

    # invalidate table numbers
    monkeypatch.setattr(connector, "check_table_numbers", lambda tns: False, raising=False)

    with pytest.raises(InvalidTableNumberError):
        connector.update_reservation_tables(1, [99, 100])

    assert connector._logged["warnings"], "Expected a warning for invalid tables"


def test_raises_on_overlapping_single_table(connector, monkeypatch):
    when = _stub_reservation_info(monkeypatch, connector, res_id=1)

    # valid numbers
    monkeypatch.setattr(connector, "check_table_numbers", lambda tns: True, raising=False)

    # mark table as unavailable (overlap)
    def check_table_available(tn, dt, spacing):
        assert tn == 5
        assert dt == when
        assert spacing == 2
        return False

    monkeypatch.setattr(connector, "check_table_available", check_table_available, raising=False)

    with pytest.raises(OverlappingReservationsError):
        connector.update_reservation_tables(1, [5])


def test_raises_on_overlapping_among_multiple_tables(connector, monkeypatch):
    when = _stub_reservation_info(monkeypatch, connector, res_id=1)
    monkeypatch.setattr(connector, "check_table_numbers", lambda tns: True, raising=False)

    # First table free, second overlaps -> should raise
    def check_table_available(tn, dt, spacing):
        assert dt == when
        return tn == 10  # 10 is free, 12 will be treated as overlap (False)

    monkeypatch.setattr(connector, "check_table_available", check_table_available, raising=False)

    with pytest.raises(OverlappingReservationsError):
        connector.update_reservation_tables(1, [10, 12])


def test_success_inserts_single_and_multiple(connector, monkeypatch):
    when = _stub_reservation_info(monkeypatch, connector, res_id=42)
    monkeypatch.setattr(connector, "check_table_numbers", lambda tns: True, raising=False)
    monkeypatch.setattr(connector, "check_table_available", lambda tn, dt, sp: True, raising=False)

    captured_calls = []

    def execute_many(sql_text, params_list, raise_on_error=True):
        captured_calls.append((sql_text.strip(), list(params_list), raise_on_error))

    monkeypatch.setattr(connector, "execute_many", execute_many, raising=False)

    # single table
    connector.update_reservation_tables(42, [3])
    assert captured_calls, "Expected INSERT to be executed"
    sql_text, params, flag = captured_calls[-1]
    assert "INSERT INTO ReservationAtTable" in sql_text
    assert params == [[42, when, 3]]
    assert flag is True

    # multiple tables
    connector.update_reservation_tables(42, [1, 2, 3])
    _, params_multi, _ = captured_calls[-1]
    assert params_multi == [[42, when, 1], [42, when, 2], [42, when, 3]]


def test_spacing_zero_is_passed_through(connector, monkeypatch):
    when = _stub_reservation_info(monkeypatch, connector, res_id=1)
    monkeypatch.setattr(connector, "check_table_numbers", lambda tns: True, raising=False)

    seen = {"calls": []}

    def check_table_available(tn, dt, spacing):
        # The function under test should pass 0 through unchanged.
        seen["calls"].append((tn, dt, spacing))
        return True

    def execute_many(sql_text, params_list, raise_on_error=True):
        return None

    monkeypatch.setattr(connector, "check_table_available", check_table_available, raising=False)
    monkeypatch.setattr(connector, "execute_many", execute_many, raising=False)

    connector.update_reservation_tables(1, [7], spacing=0)
    assert seen["calls"] == [(7, when, 0)], "Expected spacing=0 to be forwarded unchanged"


def test_execute_many_errors_are_reraised(connector, monkeypatch):
    _stub_reservation_info(monkeypatch, connector, res_id=1)
    monkeypatch.setattr(connector, "check_table_numbers", lambda tns: True, raising=False)
    monkeypatch.setattr(connector, "check_table_available", lambda tn, dt, sp: True, raising=False)

    class Boom(Exception):
        pass

    def execute_many(*args, **kwargs):
        raise Boom("insert failed")

    monkeypatch.setattr(connector, "execute_many", execute_many, raising=False)

    with pytest.raises(Boom):
        connector.update_reservation_tables(1, [1, 2])

    assert connector._logged["errors"], "Expected error to be logged when insert fails"
