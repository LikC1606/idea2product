"""Generated module: app"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Generated Application
# Build a todo list app

@app.route('/')
def index():
    return jsonify({
        'app': 'Generated Application',
        'features': ["List all items"]
    })

if __name__ == '__main__':
    app.run(debug=True)
