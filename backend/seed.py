# backend/seed.py
import os
from flask import Flask
from models import db, NGO, Donation, User

# Create a minimal Flask app here so we can init SQLAlchemy without importing app.py
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'csp.db')

def make_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def seed():
    app = make_app()
    with app.app_context():
        db.create_all()

        # Seed NGOs if none exist
        if NGO.query.count() == 0:
            ngos = [
                NGO(name="Hope For All", location="Mumbai", category="Health",
                    summary="Primary healthcare and camps", verified=True,
                    details="We run primary health camps, immunization drives."),
                NGO(name="Shelter Home", location="Delhi", category="Shelter",
                    summary="Shelter and rehabilitation", verified=True,
                    details="We run shelters for vulnerable groups."),
                NGO(name="FoodShare", location="Bengaluru", category="Hunger",
                    summary="Food distribution to needy", verified=False,
                    details="Daily food distribution in urban slums."),
                NGO(name="EduGrowth", location="Kolkata", category="Education",
                    summary="Scholarships and schools", verified=True,
                    details="Scholarships and learning support for children.")
            ]
            db.session.add_all(ngos)
            db.session.commit()
            print("Seeded NGOs")

        # Seed users
        if User.query.count() == 0:
            admin = User(email="admin@charityhub.demo", name="Admin")
            admin.set_password("adminpass")
            admin.is_admin = True
            user = User(email="user@charityhub.demo", name="User")
            user.set_password("userpass")
            db.session.add_all([admin, user])
            db.session.commit()
            print("Seeded users")

        # Seed donations
        if Donation.query.count() == 0:
            d1 = Donation(donor_name="Alice", donor_email="a@a.com", ngo_id=1, amount=500.0, txn_id="TXN-ALICE1")
            d2 = Donation(donor_name="Bob", donor_email="b@b.com", ngo_id=2, amount=1200.0, txn_id="TXN-BOB1")
            db.session.add_all([d1, d2])
            db.session.commit()
            print("Seeded donations")

    print("Seeding finished. DB file at:", os.path.join(BASE_DIR, 'csp.db'))

if __name__ == '__main__':
    seed()
