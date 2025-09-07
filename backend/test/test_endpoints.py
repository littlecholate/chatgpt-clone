from app.db.schema.user import UserInCreate

def test_health_endpoint(client):
    """
    Tests the basic health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Running...."}

def test_signup_endpoint(client):
    """
    Tests the user signup endpoint.
    """
    signup_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword"
    }
    response = client.post("/auth/signup", json=signup_data)
    
    assert response.status_code == 201
    user_data = response.json()
    assert "username" in user_data
    assert "email" in user_data
    assert user_data["email"] == "test@example.com"
    # Password should be hashed and not returned
    assert "password" not in user_data

def test_signup_existing_user(client):
    """
    Tests that a user cannot sign up with an existing email.
    """
    # First, sign up the user
    signup_data = {
        "username": "testuser",
        "email": "duplicate@example.com",
        "password": "password"
    }
    client.post("/auth/signup", json=signup_data)

    # Then, try to sign up with the same email again
    response = client.post("/auth/signup", json=signup_data)
    
    assert response.status_code == 400
    assert response.json() == {"detail": "Please Login"}