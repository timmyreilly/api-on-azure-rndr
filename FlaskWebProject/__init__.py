"""
The flask application package.
"""

from flask import Flask, request, render_template
app = Flask(__name__)

import FlaskWebProject.views