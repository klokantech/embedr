"""Script which starts embed aplication"""

import os

from app import app_factory

app = app_factory()

if __name__ == "__main__":
    app.run(host=app.config['HOST'], port=app.config['PORT'])
