from flask import Flask, request, jsonify
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory storage for notes
notes = []

@app.route('/notes', methods=['POST'])
def save_note():
    data = request.get_json()
    if 'content' not in data or not data['content'].strip():
        return jsonify({'error': 'Invalid note content'}), 400
    
    note = {
        'id': str(uuid.uuid4()),
        'content': data['content'],
        'created_at': datetime.now().isoformat()
    }
    notes.append(note)
    return jsonify(note), 201

@app.route('/notes', methods=['GET'])
def get_notes():
    return jsonify(notes)

if __name__ == "__main__":
    app.run(debug=True)