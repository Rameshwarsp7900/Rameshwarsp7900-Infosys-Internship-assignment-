import pytest
import os
import sys
import json
from io import BytesIO

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'criterion'))

from backend.app import app, session_data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_leaderboard_empty(client):
    session_data["results"] = []
    session_data["alerts"] = []
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_upload_mock(client):
    session_data["results"] = []
    session_data["alerts"] = []
    data = {
        'file': (BytesIO(b"dummy audio"), 'test.mp3'),
        'agent_name': 'Test Agent'
    }
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json["agent_name"] == "Test Agent"
    assert len(session_data["results"]) == 1

def test_api_batch_mock(client):
    session_data["results"] = []
    session_data["alerts"] = []
    data = {
        'files': [
            (BytesIO(b"audio 1"), 'file1.mp3'),
            (BytesIO(b"audio 2"), 'file2.mp3')
        ],
        'agent_name': 'Batch Agent'
    }
    response = client.post('/api/batch', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert len(response.get_json()) == 2
    assert len(session_data["results"]) == 2

def test_api_leaderboard_populated(client):
    # Already populated from test_api_batch_mock
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    res_json = response.get_json()
    assert len(res_json) == 1
    assert res_json[0]["name"] == "Batch Agent"

def test_api_clear(client):
    response = client.post('/api/clear')
    assert response.status_code == 200
    assert len(session_data["results"]) == 0
    assert len(session_data["alerts"]) == 0

def test_api_alerts(client):
    client.post('/api/clear')
    data = {
        'file': (BytesIO(b"fail me"), 'fail.mp3'),
        'agent_name': 'Bad Agent'
    }
    client.post('/api/upload', data=data, content_type='multipart/form-data')
    response = client.get('/api/alerts')
    assert response.status_code == 200
    assert len(response.get_json()) >= 1
