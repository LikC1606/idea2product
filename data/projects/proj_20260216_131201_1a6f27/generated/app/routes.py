from flask import Blueprint, request, jsonify
from datetime import datetime

routes = Blueprint('routes', __name__)

notes = []  # In-memory storage for notes

@routes.route('/notes', methods=['POST'])
def save_note():
    content = request.json.get('content')
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    note_id = len(notes) + 1
    created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    note = {"id": note_id, "content": content, "created_at": created_at}
    notes.append(note)
    return jsonify(note), 201

@routes.route('/notes', methods=['GET'])
def get_notes():
    return jsonify(notes), 200
```

```python