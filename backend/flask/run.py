import os
from app import create_app
from utils.config import Config

if __name__ == '__main__':
    app = create_app(Config)
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT')), debug=True)
