#!venv/bin/python

"""Script for start of aplication in debug server"""

from app import app

app.run(debug = True, host='0.0.0.0')
