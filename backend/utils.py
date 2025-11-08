# backend/utils.py
from flask import jsonify
def to_dict(model):
    d = {}
    for c in model.__table__.columns:
        val = getattr(model, c.name)
        if hasattr(val, 'isoformat'):
            val = val.isoformat()
        d[c.name] = val
    return d

def api_ok(payload=None):
    return jsonify({'success': True, **(payload or {})})
