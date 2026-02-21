import os
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print("=" * 50)
    print("笔记应用已启动！")
    print(f"访问地址: http://localhost:{port}")
    print(f"环境: {app.config.get('ENV', 'development')}")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)
