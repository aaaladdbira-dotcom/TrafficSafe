from app import create_app
from extensions import db
from models.accident import Accident

app, socketio = create_app()
ctx = app.app_context()
ctx.push()

print('Testing filters data structure:')
locations = [r[0] for r in db.session.query(Accident.location).distinct().all()]
delegations = [r[0] for r in db.session.query(Accident.delegation).distinct().all() if r[0]]
causes = [r[0] for r in db.session.query(Accident.cause).distinct().all() if r[0]]
severities = [r[0] for r in db.session.query(Accident.severity).distinct().all() if r[0]]

payload = {
    'locations': sorted([l for l in locations if l]),
    'delegations': sorted([d for d in delegations if d]),
    'causes': sorted([c for c in causes if c]),
    'severities': sorted([s for s in severities if s])
}

print(f"Locations: {len(payload['locations'])}")
print(f"Delegations: {len(payload['delegations'])}")
print(f"Causes: {len(payload['causes'])}")
print(f"Severities: {len(payload['severities'])}")
print(f"\nSample delegations: {payload['delegations'][:10]}")
print(f"Sample causes: {payload['causes']}")
print(f"Sample severities: {payload['severities']}")
