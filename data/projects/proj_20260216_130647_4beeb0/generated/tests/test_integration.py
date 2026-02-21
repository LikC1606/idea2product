import pytest
from app.routes import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_frontend_to_backend_integration(client):
    # Step 1: Add a note via API
    add_response = client.post('/notes', json={'content': 'Integration test note'})
    assert add_response.status_code == 200
    note = add_response.get_json()
    assert note['content'] == 'Integration test note'

    # Step 2: Fetch notes via API and check if the added note exists
    get_response = client.get('/notes')
    assert get_response.status_code == 200
    notes = get_response.get_json()
    assert any(n['content'] == 'Integration test note' for n in notes)