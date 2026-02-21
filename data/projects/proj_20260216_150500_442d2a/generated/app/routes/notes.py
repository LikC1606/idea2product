@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    notes = Note.query.filter(
        (Note.title.ilike(f'%{query}%')) | (Note.content.ilike(f'%{query}%'))
    ).all()

    return jsonify([note.to_dict() for note in notes]), 200