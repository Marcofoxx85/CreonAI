from fastapi.testclient import TestClient
from backend.main2 import app

client = TestClient(app)

def test_register():
    response = client.post("/register", data={
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert "registered" in response.text.lower()

def test_login():
    response = client.post("/login", data={
        "username": "testuser1",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert "welcome" in response.text.lower()
