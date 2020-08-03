from flask_login import UserMixin
from gmail_flask import db

# Models created in Flask-SQLAlchemy are represented by classes
# which then translate to tables in a database


class User(UserMixin, db.Model):
    # primary keys are required by SQLAlchemy
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
