from flask import Flask, jsonify, send_from_directory, g
import os

def create_app(options=None):
    app = Flask(__name__)
    app.config.from_envvar('APP_SETTINGS')
    #app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # apply any configuration override options
    if options is not None:
      for key, value in options.items():
        app.config[key] = value

    return app
