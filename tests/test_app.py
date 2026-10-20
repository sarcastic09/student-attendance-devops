import os
import tempfile
import pytest

@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_PATH", path)
    import app as app_module
    app_module.DB_PATH = path
    app_module.init_db()
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with app_module.app.test_client() as test_client:
        yield test_client
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Attendance System" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_add_student(client):
    response = client.post("/students/add", data={"roll_number": "A001", "name": "Asha Patil", "course": "AI & DS"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Asha Patil" in response.data


def test_duplicate_roll_number_is_rejected(client):
    payload = {"roll_number": "A001", "name": "Asha Patil", "course": "AI & DS"}
    client.post("/students/add", data=payload)
    response = client.post("/students/add", data={**payload, "name": "Another Student"}, follow_redirects=True)
    assert b"already exists" in response.data


def test_attendance_can_be_marked(client):
    client.post("/students/add", data={"roll_number": "A001", "name": "Asha Patil", "course": "AI & DS"})
    response = client.post("/attendance", data={"attendance_date": "2026-10-20", "status_1": "Present"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Present" in response.data
