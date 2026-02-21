import pytest
from app.routes import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_post_note_endpoint(client):
    response = client.post('/notes', json={'content': 'Test note'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert 'content' in data
    assert 'created_at' in data
    assert data['content'] == 'Test note'

def test_get_notes_endpoint(client):
    client.post('/notes', json={'content': 'Note 1'})
    client.post('/notes', json={'content': 'Note 2'})
    response = client.get('/notes')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert data[0]['content'] == 'Note 1'
    assert data[1]['content'] == 'Note 2'
```

```python