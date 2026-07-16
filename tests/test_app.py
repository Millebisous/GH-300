from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.app import app


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)

    with TestClient(app) as test_client:
        yield test_client

    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_redirect_path = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_redirect_path


def test_signup_participant_adds_email_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == f"Signed up {email} for {activity_name}"

    activity = client.get("/activities").json()[activity_name]
    assert email in activity["participants"]


def test_unregister_participant_removes_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == f"Unregistered {email} from {activity_name}"

    activity = client.get("/activities").json()[activity_name]
    assert email not in activity["participants"]


def test_signup_rejects_duplicate_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_static_index_contains_daily_fortune_section(client):
    # Act
    response = client.get("/static/index.html")

    # Assert
    assert response.status_code == 200
    html = response.text
    assert "Daily Fortune (Omikuji)" in html
    assert "fortune-divider" in html


def test_static_app_js_uses_only_lucky_and_neutral_fortunes(client):
    # Act
    response = client.get("/static/app.js")

    # Assert
    assert response.status_code == 200
    app_js = response.text
    assert "tone" in app_js
    assert "unlucky" not in app_js.lower()


def test_static_index_contains_fuel_checker_section(client):
    response = client.get("/static/index.html")

    assert response.status_code == 200
    html = response.text
    assert "Fuel Checker" in html
    assert "fuel-divider" in html
    assert "fuel-button" in html


def test_fuel_trends_endpoint_groups_by_fuel_type_for_last_six_months(client, monkeypatch):
    sample_payload = {
        "result": {
            "resources": [
                {"name": "FuelCheck Price History January 2026", "url": "https://example.test/jan.csv"},
                {"name": "FuelCheck Price History February 2026", "url": "https://example.test/feb.csv"},
                {"name": "FuelCheck Price History March 2026", "url": "https://example.test/mar.csv"},
                {"name": "FuelCheck Price History April 2026", "url": "https://example.test/apr.csv"},
                {"name": "FuelCheck Price History May 2026", "url": "https://example.test/may.csv"},
                {"name": "FuelCheck Price History June 2026", "url": "https://example.test/jun.csv"},
            ]
        }
    }

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(self._payload).encode("utf-8")

        def json(self):
            return self._payload

    def fake_urlopen(request, timeout=30):
        if "package_show" in request.full_url:
            return FakeResponse(sample_payload)
        if request.full_url.endswith("jan.csv"):
            return FakeResponse(
                {
                    "rows": [
                        ["FuelCode", "PriceUpdatedDate", "Price"],
                        ["U91", "2026-01-01 00:00:00", "170.5"],
                        ["U91", "2026-01-02 00:00:00", "171.0"],
                        ["P98", "2026-01-01 00:00:00", "195.0"],
                    ]
                }
            )
        return FakeResponse({"rows": []})

    monkeypatch.setattr(app_module.urllib.request, "urlopen", fake_urlopen)

    response = client.get("/fuel-trends")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["months"]) == 6
    assert sorted(payload["fuelTypes"]) == ["P98", "U91"]
    assert payload["fuelTypes"]["U91"]["points"][0]["date"] == "2026-01-01"
    assert payload["fuelTypes"]["U91"]["points"][0]["average"] == 170.5
    assert payload["fuelTypes"]["P98"]["points"][0]["average"] == 195.0


def test_fuel_trends_include_price_drop_prediction(client, monkeypatch):
    sample_payload = {
        "result": {
            "resources": [
                {"name": "FuelCheck Price History January 2026", "url": "https://example.test/jan.csv"},
                {"name": "FuelCheck Price History February 2026", "url": "https://example.test/feb.csv"},
                {"name": "FuelCheck Price History March 2026", "url": "https://example.test/mar.csv"},
                {"name": "FuelCheck Price History April 2026", "url": "https://example.test/apr.csv"},
                {"name": "FuelCheck Price History May 2026", "url": "https://example.test/may.csv"},
                {"name": "FuelCheck Price History June 2026", "url": "https://example.test/jun.csv"},
            ]
        }
    }

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(self._payload).encode("utf-8")

        def json(self):
            return self._payload

    def fake_urlopen(request, timeout=30):
        if "package_show" in request.full_url:
            return FakeResponse(sample_payload)
        if request.full_url.endswith("jan.csv"):
            return FakeResponse(
                {
                    "rows": [
                        ["FuelCode", "PriceUpdatedDate", "Price"],
                        ["U91", "2026-01-01 00:00:00", "170.5"],
                        ["U91", "2026-01-02 00:00:00", "171.0"],
                        ["U91", "2026-01-03 00:00:00", "169.0"],
                        ["U91", "2026-01-04 00:00:00", "170.0"],
                    ]
                }
            )
        return FakeResponse({"rows": []})

    monkeypatch.setattr(app_module.urllib.request, "urlopen", fake_urlopen)

    response = client.get("/fuel-trends")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fuelTypes"]["U91"]["trend"]["overall"] in {"rising", "mixed", "falling"}
    assert payload["fuelTypes"]["U91"]["trend"]["average_weeks_between_dips"] >= 0
    assert payload["fuelTypes"]["U91"]["trend"]["next_predicted_drop_week"]

