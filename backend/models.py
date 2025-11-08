# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(150))
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class NGO(db.Model):
    __tablename__ = 'ngos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(120))
    category = db.Column(db.String(100))
    summary = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)
    details = db.Column(db.Text)  # longer description

class Donation(db.Model):
    __tablename__ = 'donations'
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(120))
    donor_email = db.Column(db.String(120))
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngos.id'))
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    txn_id = db.Column(db.String(120))
    ngo = db.relationship('NGO')
