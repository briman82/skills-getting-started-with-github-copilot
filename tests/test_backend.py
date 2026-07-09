from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities_state():
    # Keep tests deterministic because the API mutates in-memory state.
    original_activities = deepcopy(app_module.activities)

    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))

    yield

    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (307, 302)
    assert response.headers["location"] == expected_location


def test_get_activities_returns_seeded_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert expected_activity in payload
    assert "participants" in payload[expected_activity]


def test_signup_adds_participant_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "new.student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {new_email} for {activity_name}"
    }
    assert activities_response.status_code == 200
    assert new_email in activities_response.json()[activity_name]["participants"]


def test_unregister_removes_participant_from_activity(client):
    # Arrange
    activity_name = "Programming Class"
    existing_email = "emma@mergington.edu"

    # Act
    unregister_response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": existing_email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {existing_email} from {activity_name}"
    }
    assert activities_response.status_code == 200
    assert existing_email not in activities_response.json()[activity_name]["participants"]
