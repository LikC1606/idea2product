import unittest
from flask import Flask, render_template
from flask_testing import TestCase

class TestFrontendComponents(TestCase):
    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True

        @app.route('/')
        def index():
            return render_template('index.html', notes=[{'content': 'Sample Note', 'created_at': '2023-10-01'}])

        @app.route('/create_note')
        def create_note():
            return render_template('create_note.html')

        @app.route('/search_results')
        def search_results():
            return render_template('search_results.html', results=[{'content': 'Search Note', 'created_at': '2023-10-01'}])

        return app

    def test_index_page(self):
        response = self.client.get('/')
        self.assert200(response)
        self.assert_template_used('index.html')
        self.assertIn(b'Sample Note', response.data)

    def test_create_note_page(self):
        response = self.client.get('/create_note')
        self.assert200(response)
        self.assert_template_used('create_note.html')

    def test_search_results_page(self):
        response = self.client.get('/search_results')
        self.assert200(response)
        self.assert_template_used('search_results.html')
        self.assertIn(b'Search Note', response.data)

if __name__ == '__main__':
    unittest.main()