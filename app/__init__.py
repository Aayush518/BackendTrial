from flask import Flask
from flask_migrate import Migrate
from .extensions import api, db
from .resources import ns
from .models import *


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///example"
    api.init_app(app)
    db.init_app(app)

    migrate = Migrate(app, db)
    make_searchable(db.metadata)


    api.add_namespace(ns)

    return app
