from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models.accident_report import AccidentReport
from models.user import User
from models.accident import Accident
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

# Helper: Only non-government users can submit

def non_gov_required():
    claims = get_jwt()
    if claims.get("role") == "government":
        abort(403, description="Government users cannot submit reports.")

# Helper: Only government users can access

def gov_required():
    claims = get_jwt()
    if claims.get("role") != "government":
        abort(403, description="Only government users allowed.")

# Submit a new accident report (non-gov users)
@reports_bp.route('/reports', methods=['POST'])
@jwt_required()
def submit_report():
    non_gov_required()
    data = request.get_json()
    required = ["date", "location", "delegation", "severity", "phone"]
    for f in required:
        if not data.get(f):
            abort(400, description=f"Missing field: {f}")
    # Phone validation
    if not data["phone"].startswith("+216") or len(data["phone"]) != 13:
        abort(400, description="Phone number must start with +216 and be Tunisia format.")
    try:
        date = datetime.fromisoformat(data["date"])
    except Exception:
        abort(400, description="Invalid date format.")
    user_id = get_jwt_identity()
    print(f"[DEBUG] Submitting report: user_id={user_id}, data={data}")
    report = AccidentReport(
        user_id=user_id,
        date=date,
        location=data["location"],
        delegation=data["delegation"],
        severity=data["severity"],
        phone=data["phone"],
        status="PENDING"
    )
    db.session.add(report)
    db.session.commit()
    print(f"[DEBUG] Report submitted: id={report.id}")
    return jsonify({"message": "Report submitted successfully.", "report_id": report.id}), 201

# Get reports (user: own, gov: all)
@reports_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_reports():
    claims = get_jwt()
    user_id = get_jwt_identity()
    print(f"[DEBUG] Fetching reports: user_id={user_id}, role={claims.get('role')}")
    if claims.get("role") == "government":
        reports = AccidentReport.query.order_by(AccidentReport.created_at.desc()).all()
    else:
        reports = AccidentReport.query.filter_by(user_id=user_id).order_by(AccidentReport.created_at.desc()).all()
    print(f"[DEBUG] Reports fetched: count={len(reports)}")
    return jsonify([
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "location": r.location,
            "delegation": r.delegation,
            "severity": r.severity,
            "phone": r.phone,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "user": {"id": r.user.id, "full_name": r.user.full_name, "email": r.user.email},
            "accident_id": r.accident_id,
            "rejection_reason": r.rejection_reason
        } for r in reports
    ])

# Get single report (user: own, gov: any)
@reports_bp.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    claims = get_jwt()
    user_id = get_jwt_identity()
    report = AccidentReport.query.get_or_404(report_id)
    if claims.get("role") != "government" and report.user_id != int(user_id):
        abort(403, description="Not authorized.")
    return jsonify({
        "id": report.id,
        "date": report.date.isoformat(),
        "location": report.location,
        "delegation": report.delegation,
        "severity": report.severity,
        "phone": report.phone,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "user": {"id": report.user.id, "full_name": report.user.full_name, "email": report.user.email},
        "accident_id": report.accident_id,
        "rejection_reason": report.rejection_reason
    })

# Confirm a report (gov only)
@reports_bp.route('/reports/<int:report_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_report(report_id):
    gov_required()
    report = AccidentReport.query.get_or_404(report_id)
    if report.status != "PENDING":
        abort(400, description="Report already processed.")
    # Create new accident
    accident = Accident(
        occurred_at=report.date,
        location=report.location,
        delegation=report.delegation,
        severity=report.severity,
        source="user_report"
    )
    db.session.add(accident)
    db.session.flush()  # Get accident.id
    report.status = "CONFIRMED"
    report.accident_id = accident.id
    db.session.commit()
    return jsonify({"message": "Report confirmed and accident created.", "accident_id": accident.id})

# Reject a report (gov only)
@reports_bp.route('/reports/<int:report_id>/reject', methods=['POST'])
@jwt_required()
def reject_report(report_id):
    gov_required()
    report = AccidentReport.query.get_or_404(report_id)
    if report.status != "PENDING":
        abort(400, description="Report already processed.")
    data = request.get_json() or {}
    reason = data.get("reason")
    report.status = "REJECTED"
    report.rejection_reason = reason
    db.session.commit()
    return jsonify({"message": "Report rejected."})
