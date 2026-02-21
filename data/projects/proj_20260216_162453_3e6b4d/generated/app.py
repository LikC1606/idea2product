"""
应用入口
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print("=" * 50)
    print(f"Flask App Started: http://localhost:{port}")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)
