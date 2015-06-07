"""Script for start of aplication in local debug mode"""

import os

#from flask_debugtoolbar import DebugToolbarExtension

from app import app_factory

app = app_factory(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config_local.py'))
#app.debug = True
#toolbar = DebugToolbarExtension()
#toolbar.init_app(app)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
