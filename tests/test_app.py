from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRoot:
    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    def test_get_all_activities(self):
        """Test that we can fetch all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Check that activities are returned
        assert len(activities) > 0
        
        # Check that expected activities exist
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        
        # Check activity structure
        chess = activities["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert isinstance(chess["participants"], list)


class TestSignup:
    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_duplicate_fails(self):
        """Test that duplicate signup fails"""
        email = "duplicate@example.com"
        
        # First signup succeeds
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email fails
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestUnregister:
    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unreg@example.com"
        
        # First, sign up
        client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_not_signed_up(self):
        """Test that unregistering when not signed up fails"""
        response = client.delete(
            "/activities/Drama Club/signup",
            params={"email": "notregistered@example.com"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestSignupAndUnregisterFlow:
    def test_full_signup_unregister_flow(self):
        """Test complete signup and unregister flow"""
        email = "flow@example.com"
        activity = "Debate Team"
        
        # Check initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant added
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant removed
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count
        assert email not in response.json()[activity]["participants"]
