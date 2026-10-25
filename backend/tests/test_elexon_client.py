from datetime import datetime, timedelta, timezone

import pytest
import requests

from app.services import elexon_client
from app.services.elexon_client import ElexonAPIError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=False):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error
        self.text = "fake response body"

    def json(self):
        if self._json_error:
            raise ValueError("bad json")
        return self._payload


def install_fake_get(monkeypatch, responses):
    """Replace requests.get with a fake that returns the given items in order."""
    calls = []
    queue = list(responses)

    def fake_get(url, params=None, timeout=None):
        calls.append({"url": url, "params": params})
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(elexon_client.requests, "get", fake_get)
    return calls


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(elexon_client.time, "sleep", lambda seconds: None)


JAN_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
JAN_2 = datetime(2026, 1, 2, tzinfo=timezone.utc)
JAN_11 = datetime(2026, 1, 11, tzinfo=timezone.utc)


def test_to_utc_string_converts_other_timezones_to_utc():
    ist = timezone(timedelta(hours=5, minutes=30))
    value = datetime(2026, 1, 1, 5, 30, tzinfo=ist)
    assert elexon_client._to_utc_string(value) == "2026-01-01T00:00:00Z"


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError):
        elexon_client._to_utc_string(datetime(2026, 1, 1))


def test_start_must_be_before_end():
    with pytest.raises(ValueError):
        elexon_client.fetch_dataset("FUELHH", JAN_2, JAN_1)


def test_range_is_split_into_windows(monkeypatch):
    calls = install_fake_get(monkeypatch, [FakeResponse(200, []), FakeResponse(200, [])])

    elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_11, chunk_days=7)

    assert len(calls) == 2
    assert calls[0]["url"] == f"{elexon_client.BASE_URL}/FUELHH/stream"
    assert calls[0]["params"]["publishDateTimeFrom"] == "2026-01-01T00:00:00Z"
    assert calls[0]["params"]["publishDateTimeTo"] == "2026-01-08T00:00:00Z"
    assert calls[1]["params"]["publishDateTimeFrom"] == "2026-01-08T00:00:00Z"
    assert calls[1]["params"]["publishDateTimeTo"] == "2026-01-11T00:00:00Z"


def test_actual_records_keep_only_wind(monkeypatch):
    payload = [
        {"fuelType": "WIND", "generation": 100},
        {"fuelType": "CCGT", "generation": 200},
        {"fuelType": "WIND", "generation": 300},
        {"fuelType": "NUCLEAR", "generation": 400},
    ]
    install_fake_get(monkeypatch, [FakeResponse(200, payload)])

    result = elexon_client.fetch_actual_wind_records(JAN_1, JAN_2)

    assert [record["generation"] for record in result] == [100, 300]


def test_temporary_server_error_is_retried(monkeypatch):
    calls = install_fake_get(
        monkeypatch,
        [FakeResponse(503), FakeResponse(200, [{"fuelType": "WIND"}])],
    )

    result = elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_2)

    assert len(calls) == 2
    assert len(result) == 1


def test_client_error_is_not_retried(monkeypatch):
    calls = install_fake_get(monkeypatch, [FakeResponse(400)])

    with pytest.raises(ElexonAPIError):
        elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_2)

    assert len(calls) == 1


def test_gives_up_after_max_attempts(monkeypatch):
    error = requests.ConnectionError("no internet")
    calls = install_fake_get(monkeypatch, [error] * elexon_client.MAX_ATTEMPTS)

    with pytest.raises(ElexonAPIError):
        elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_2)

    assert len(calls) == elexon_client.MAX_ATTEMPTS


def test_invalid_json_raises_clear_error(monkeypatch):
    install_fake_get(monkeypatch, [FakeResponse(200, json_error=True)])

    with pytest.raises(ElexonAPIError):
        elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_2)


def test_data_key_payload_is_accepted(monkeypatch):
    install_fake_get(monkeypatch, [FakeResponse(200, {"data": [{"a": 1}]})])

    assert elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_2) == [{"a": 1}]


def test_unexpected_payload_raises_error(monkeypatch):
    install_fake_get(monkeypatch, [FakeResponse(200, {"unexpected": 1})])

    with pytest.raises(ElexonAPIError):
        elexon_client.fetch_dataset("FUELHH", JAN_1, JAN_2)