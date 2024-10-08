import os
from app import create_app
from utils.config import DevConfig

if __name__ == '__main__':
    app = create_app(DevConfig)
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT')), debug=True)
