
# Imports and Blueprint definition must come first
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify, Response
from extensions import db
from models.accident import Accident
from models.user import User
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from utils.errors import ForbiddenError, NotFoundError, DatabaseError, ValidationError, success_response, paginated_response
from utils.validators import PaginationValidator, DateRangeValidator, FilterValidator
from extensions import limiter

blp = Blueprint("accidents", "accidents", url_prefix="/api/v1/accidents")


@blp.route('/<int:accident_id>', methods=['PATCH'])
@jwt_required()
@limiter.limit("10 per minute")
def update_accident(accident_id):
    print("[DEBUG] update accident id =", accident_id)
    if not isinstance(accident_id, int) or accident_id <= 0:
        return {"error": "Invalid accident ID"}, 400
    """Update an accident. Government users only.
    
    Supports updating: location, delegation, severity, cause
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'government':
        raise ForbiddenError("Only government users can update accidents")
    
    accident = Accident.query.get(accident_id)
    if not accident:
        raise NotFoundError("Accident", accident_id)
    
    data = request.get_json() or {}
    allowed_fields = ['location', 'delegation', 'severity', 'cause']
    
    for field in allowed_fields:
        if field in data:
            setattr(accident, field, data[field])
    
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise DatabaseError(f"Failed to update accident: {str(e)}")
    
    return success_response(
        data={"id": accident.id},
        message="Accident updated successfully"
    )


@blp.route("")
@jwt_required()
@limiter.limit("120 per minute")
def list_accidents():
    """List accidents with optional filters and pagination.

    Query params supported:
      - location: exact match on location/governorate string
      - delegation: exact match on delegation
      - cause: exact match on cause
      - severity: exact match on severity (fatal/serious/minor)
      - start_date, end_date: ISO date/time strings to filter occurred_at
      - page: 1-based page number (default 1)
      - per_page: items per page (default 20, max 100)
    """
    try:
        page, per_page = PaginationValidator.validate()
        start_date, end_date = DateRangeValidator.validate()
    except ValidationError as e:
        raise e
    
    q = Accident.query

    # Filtering params
    location = FilterValidator.validate_string('location', max_length=255)
    delegation = FilterValidator.validate_string('delegation', max_length=255)
    cause = FilterValidator.validate_string('cause', max_length=255)
    severity = FilterValidator.validate_enum('severity', ['fatal', 'serious', 'minor'])

    if location:
        q = q.filter(Accident.governorate == location)
    if delegation:
        q = q.filter(Accident.delegation == delegation)
    if cause:
        q = q.filter(Accident.cause == cause)
    if severity:
        q = q.filter(Accident.severity == severity)

    # Date range filtering
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            q = q.filter(Accident.occurred_at >= sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            q = q.filter(Accident.occurred_at <= ed)
        except Exception:
            pass

    total = q.count()
    items = q.order_by(Accident.occurred_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    def fmt(a):
        return {
            "id": a.id,
            "date": a.occurred_at.isoformat() if a.occurred_at is not None else None,
            "date_human": a.occurred_at.strftime("%Y-%m-%d %H:%M") if a.occurred_at is not None else None,
            "location": a.location,
            "governorate": getattr(a, 'governorate', None) or a.location,
            "delegation": getattr(a, 'delegation', None),
            "severity": a.severity,
            "cause": a.cause,
        }

    return paginated_response(
        items=[fmt(a) for a in items],
        page=page,
        per_page=per_page,
        total=total,
        message="Accidents retrieved successfully"
    )


@blp.route("/filters")
@jwt_required()
@limiter.limit("120 per minute")
def accidents_filters():
    """Return distinct values for location/governorate, delegation, cause, severity to populate UI selects."""
    governorates = [r[0] for r in db.session.query(Accident.governorate).distinct().all() if r[0]]
    delegations = [r[0] for r in db.session.query(Accident.delegation).distinct().all() if r[0]]
    causes = [r[0] for r in db.session.query(Accident.cause).distinct().all() if r[0]]
    severities = [r[0] for r in db.session.query(Accident.severity).distinct().all() if r[0]]

    payload = {
        "locations": sorted([g for g in governorates if g]),
        "delegations": sorted([d for d in delegations if d]),
        "causes": sorted([c for c in causes if c]),
        "severities": sorted([s for s in severities if s]),
    }
    return success_response(data=payload, message="Filter options retrieved")


@blp.route('/export')
@jwt_required()
@limiter.limit("5 per minute")
def export_csv():
    """Export filtered accidents as CSV.

    Accepts same query params as list_accidents.
    """
    q = Accident.query
    location = FilterValidator.validate_string('location', max_length=255)
    delegation = FilterValidator.validate_string('delegation', max_length=255)
    cause = FilterValidator.validate_string('cause', max_length=255)
    severity = FilterValidator.validate_enum('severity', ['fatal', 'serious', 'minor'])
    start_date, end_date = DateRangeValidator.validate()

    if location:
        q = q.filter(Accident.governorate == location)
    if delegation:
        q = q.filter(Accident.delegation == delegation)
    if cause:
        q = q.filter(Accident.cause == cause)
    if severity:
        q = q.filter(Accident.severity == severity)
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            q = q.filter(Accident.occurred_at >= sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            q = q.filter(Accident.occurred_at <= ed)
        except Exception:
            pass

    items = q.order_by(Accident.occurred_at.desc()).all()

    # Build CSV
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "occurred_at", "severity", "governorate", "delegation", "cause"])
    for a in items:
        writer.writerow([
            a.id,
            a.occurred_at.isoformat() if a.occurred_at else '',
            a.severity,
            getattr(a, 'governorate', None) or a.location or '',
            getattr(a, 'delegation', None) or '',
            a.cause or ''
        ])

    resp = Response(output.getvalue(), mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'attachment; filename=accidents_export.csv'
    return resp


@blp.route('/batch', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def batch_create_accidents():
    """Create multiple accidents in a single request.
    
    Request body:
    {
      "items": [
        {
          "location": "Tunis",
          "governorate": "Tunis",
          "delegation": "Tunis",
          "severity": "serious",
          "cause": "Speeding"
        },
        ...
      ]
    }
    
    Government users only. Max 100 items per request.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'government':
        raise ForbiddenError("Only government users can create accidents")
    
    data = request.get_json() or {}
    items = data.get('items', [])
    
    from utils.batch import BatchAccidentCreator
    result = BatchAccidentCreator.create_batch(items)
    
    return success_response(
        data=result,
        message=f"Successfully created {result['created_count']} accidents",
        status_code=201
    )

