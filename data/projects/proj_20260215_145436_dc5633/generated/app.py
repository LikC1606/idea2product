"""Generated module: app"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Generated Application
# Build an ACM problem-solving website

@app.route('/')
def index():
    return jsonify({
        'app': 'Generated Application',
        'features': ["Basic Functionality"]
    })

if __name__ == '__main__':
    app.run(debug=True)
