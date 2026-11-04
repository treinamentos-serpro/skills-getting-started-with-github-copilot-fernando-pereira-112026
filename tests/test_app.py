from src.app import activities


class TestRoot:
    def test_root_redirects_to_static_index(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == set(activities.keys())

    def test_activity_has_expected_structure(self, client):
        data = client.get("/activities").json()
        chess = data["Chess Club"]
        assert chess["description"] == (
            "Learn strategies and compete in chess tournaments"
        )
        assert chess["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess["max_participants"] == 12
        assert "michael@mergington.edu" in chess["participants"]


class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "message": "Signed up newstudent@mergington.edu for Chess Club"
        }
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Student already signed up for this activity"
        )

    def test_signup_full_activity_returns_400(self, client):
        activity = activities["Chess Club"]
        for i in range(activity["max_participants"] - len(activity["participants"])):
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": f"filler{i}@mergington.edu"},
            )
            assert response.status_code == 200

        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "onetoomany@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"


class TestRemoveParticipant:
    def test_remove_success(self, client):
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "message": "Removed michael@mergington.edu from Chess Club"
        }
        assert (
            "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        )

    def test_remove_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Nonexistent Club/participants",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_not_signed_up_returns_404(self, client):
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "ghost@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Student is not signed up for this activity"
        )


class TestStateIsolation:
    def test_signup_from_other_test_was_rolled_back(self, client):
        """The autouse fixture must restore participants between tests."""
        assert len(activities["Chess Club"]["participants"]) == 2
