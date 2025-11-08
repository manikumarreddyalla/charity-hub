# backend/app.py  (replace your existing file with this)
import os
from flask import Flask, request, jsonify, send_from_directory, send_file, url_for
from flask_cors import CORS
from models import db, User, NGO, Donation
from recommender import TFIDFRecommender
from auth import create_token, decode_token
from utils import to_dict, api_ok
from datetime import datetime
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

# Create Flask app
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# DB config
db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'csp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Recommender instance (global)
recommender = TFIDFRecommender()

def fit_recommender():
    """Load all NGOs and fit the TF-IDF recommender. Safe to call multiple times."""
    ngos = []
    with app.app_context():
        for n in NGO.query.all():
            text = (n.summary or '') + ' ' + (n.details or '')
            ngos.append({'id': n.id, 'text': text})
    recommender.fit(ngos)

# ---------- Frontend routes ----------
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # serve static files (html, css, js)
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    # fallback
    return app.send_static_file('index.html')

# ---------- Auth ----------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    admin_code = data.get('admin_code')
    if not (email and password and name):
        return jsonify({'success': False, 'error': 'missing fields'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'email exists'}), 400
    user = User(email=email, name=name)
    user.set_password(password)
    if admin_code and admin_code == os.environ.get('CSP_ADMIN_CODE', 'let-me-admin'):
        user.is_admin = True
    db.session.add(user)
    db.session.commit()
    token = create_token(user)
    return jsonify({'success': True, 'token': token, 'user': {'email': user.email, 'name': user.name, 'is_admin': user.is_admin}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not (email and password):
        return jsonify({'success': False, 'error': 'missing fields'}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': 'invalid credentials'}), 401
    token = create_token(user)
    return jsonify({'success': True, 'token': token, 'user': {'email': user.email, 'name': user.name, 'is_admin': user.is_admin}})

def auth_user_from_header():
    auth = request.headers.get('Authorization', None)
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    payload = decode_token(parts[1])
    if not payload:
        return None
    return User.query.get(payload['sub'])

# ---------- NGO endpoints ----------
@app.route('/api/ngos', methods=['GET'])
def list_ngos():
    ngos = NGO.query.all()
    return jsonify([{
      'id': n.id, 'name': n.name, 'location': n.location,
      'category': n.category, 'summary': n.summary, 'verified': n.verified
    } for n in ngos])

@app.route('/api/ngos/<int:ngo_id>', methods=['GET'])
def get_ngo(ngo_id):
    n = NGO.query.get(ngo_id)
    if not n:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'id': n.id, 'name': n.name, 'location': n.location, 'category': n.category, 'summary': n.summary, 'details': n.details, 'verified': n.verified})

@app.route('/api/admin/ngos', methods=['POST'])
def create_ngo():
    user = auth_user_from_header()
    if not user or not user.is_admin:
        return jsonify({'error': 'admin required'}), 403
    data = request.get_json() or {}
    required = data.get('name')
    if not required:
        return jsonify({'error': 'name required'}), 400
    n = NGO(name=data.get('name'), location=data.get('location'), category=data.get('category'),
            summary=data.get('summary'), details=data.get('details'), verified=bool(data.get('verified', False)))
    db.session.add(n)
    db.session.commit()
    # update recommender index
    fit_recommender()
    return jsonify({'success': True, 'id': n.id})

@app.route('/api/admin/ngos/<int:ngo_id>', methods=['PUT'])
def update_ngo(ngo_id):
    user = auth_user_from_header()
    if not user or not user.is_admin:
        return jsonify({'error': 'admin required'}), 403
    n = NGO.query.get(ngo_id)
    if not n:
        return jsonify({'error': 'not found'}), 404
    data = request.get_json() or {}
    for key in ['name','location','category','summary','details','verified']:
        if key in data:
            setattr(n, key, data[key])
    db.session.commit()
    fit_recommender()
    return jsonify({'success': True})

@app.route('/api/admin/ngos/<int:ngo_id>', methods=['DELETE'])
def delete_ngo(ngo_id):
    user = auth_user_from_header()
    if not user or not user.is_admin:
        return jsonify({'error': 'admin required'}), 403
    n = NGO.query.get(ngo_id)
    if not n:
        return jsonify({'error': 'not found'}), 404
    db.session.delete(n)
    db.session.commit()
    fit_recommender()
    return jsonify({'success': True})

# ---------- Donation endpoints ----------
@app.route('/api/donate', methods=['POST'])
def donate():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    ngo_id = data.get('ngo_id')
    amount = data.get('amount')
    if not (name and email and ngo_id and amount):
        return jsonify({'success': False, 'error': 'missing fields'}), 400
    ngo = NGO.query.get(ngo_id)
    if not ngo:
        return jsonify({'success': False, 'error': 'invalid NGO'}), 400
    txn = 'TXN-' + uuid.uuid4().hex[:12].upper()
    donation = Donation(donor_name=name, donor_email=email, ngo_id=ngo_id, amount=float(amount), txn_id=txn)
    db.session.add(donation)
    db.session.commit()
    receipt_path = generate_receipt_pdf(donation.id)
    download_url = url_for('download_receipt', filename=os.path.basename(receipt_path), _external=True)
    return jsonify({'success': True, 'donation_id': donation.id, 'txn_id': txn, 'receipt_url': download_url})

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    rows = db.session.query(NGO.name, db.func.sum(Donation.amount))\
         .join(Donation, NGO.id==Donation.ngo_id)\
         .group_by(NGO.id).all()
    by_ngo = [{'name': r[0], 'total': float(r[1] or 0)} for r in rows]
    recent = Donation.query.order_by(Donation.timestamp.desc()).limit(10).all()
    recent_list = [{
      'donor_name': d.donor_name,
      'ngo_name': d.ngo.name if d.ngo else '',
      'amount': d.amount,
      'date': d.timestamp.isoformat(),
      'txn_id': d.txn_id
    } for d in recent]
    return jsonify({'by_ngo': by_ngo, 'recent': recent_list})

# ---------- Recommender endpoint ----------
@app.route('/api/recommendations', methods=['GET'])
def recommendations():
    ngo_id = request.args.get('ngo_id', type=int)
    verified_ids = [n.id for n in NGO.query.filter_by(verified=True).all()]
    rec_ids = recommender.recommend(ngo_id=ngo_id, top_k=6, prefer_verified_ids=verified_ids)
    ngos = NGO.query.filter(NGO.id.in_(rec_ids)).all()
    id_to_ngo = {n.id: n for n in ngos}
    data = [ {'id': rid, 'name': id_to_ngo[rid].name, 'summary': id_to_ngo[rid].summary} for rid in rec_ids if rid in id_to_ngo]
    return jsonify({'recommendations': data})

# ---------- Receipts ----------
RECEIPT_DIR = os.path.join(BASE_DIR, 'receipts')
os.makedirs(RECEIPT_DIR, exist_ok=True)

def generate_receipt_pdf(donation_id):
    d = Donation.query.get(donation_id)
    filename = f"receipt_{donation_id}_{int(datetime.utcnow().timestamp())}.pdf"
    path = os.path.join(RECEIPT_DIR, filename)
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height-80, "Charity Hub — Donation Receipt")
    c.setFont("Helvetica", 12)
    c.drawString(50, height-120, f"Donor: {d.donor_name}")
    c.drawString(50, height-140, f"Email: {d.donor_email}")
    c.drawString(50, height-160, f"NGO: {d.ngo.name if d.ngo else ''}")
    c.drawString(50, height-180, f"Amount: INR {d.amount:.2f}")
    c.drawString(50, height-200, f"Transaction ID: {d.txn_id}")
    c.drawString(50, height-220, f"Date: {d.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, height-260, "Thank you for your generous donation.")
    c.showPage()
    c.save()
    return path

@app.route('/receipts/<path:filename>', methods=['GET'])
def download_receipt(filename):
    return send_file(os.path.join(RECEIPT_DIR, filename), mimetype='application/pdf', as_attachment=True)

# ---------- App init helper ----------
def init_app_once():
    # create DB tables and fit recommender (call this at startup)
    with app.app_context():
        db.create_all()
        fit_recommender()

if __name__ == '__main__':
    # only run initialization when executed directly
    init_app_once()
    app.run(port=5000, debug=True)
