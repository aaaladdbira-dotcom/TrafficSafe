from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from extensions import db
from models.accident import Accident
from models.import_batch import ImportBatch
from datetime import datetime
import csv
import io
import logging
import os

import_api = Blueprint("import_api", __name__, url_prefix="/upload/import")

# Simple file-based audit logger for import/delete actions.
# Writes to instance/import_audit.log so it's persisted outside the DB and
# doesn't require migrations. Format: ISO timestamp | actor_id | role | action | details
logger = logging.getLogger("import_audit")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    try:
        os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)
    except Exception:
        # instance dir may already be created elsewhere; ignore errors
        pass
    # determine path relative to project root: use the instance/ folder sibling to app modules
    log_path = os.path.join(os.path.dirname(__file__), "..", "instance", "import_audit.log")
    fh = logging.FileHandler(log_path)
    fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
    logger.addHandler(fh)

@import_api.route("", methods=["POST"])
@jwt_required()
def import_csv():
    claims = get_jwt()
    if claims.get("role") != "government":
        return jsonify({"message": "Forbidden"}), 403

    file = request.files.get("file")
    if not file:
        return jsonify({"message": "No file provided"}), 400

    # Read CSV text
    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    # Flexible column matching: accept common aliases so users can upload varied CSVs
    aliases = {
        'occurred_at': ['occurred_at', 'occurred', 'date', 'datetime', 'timestamp', 'occurred at'],
        'severity': ['severity', 'sev', 'level'],
        'location': ['location', 'governorate', 'state', 'region', 'place'],
        'delegation': ['delegation', 'deleg', 'municipality', 'commune', 'district'],
        'cause': ['cause', 'reason', 'accident_cause'],
    }

    # Build a mapping from canonical name -> actual CSV column name
    csv_fields = [f.strip().lower() for f in (reader.fieldnames or [])]
    column_map = {}
    missing = []
    for key, keys in aliases.items():
        found = None
        for alias in keys:
            if alias.lower() in csv_fields:
                # find actual original header with that lowercase
                for original in reader.fieldnames:
                    if original.strip().lower() == alias.lower():
                        found = original
                        break
                if found:
                    break
        if found:
            column_map[key] = found
        else:
            # only require the three core fields
            if key in ('occurred_at', 'severity', 'location'):
                missing.append(key)

    if missing:
        return jsonify({
            'message': 'Missing required columns',
            'missing_columns': missing,
            'available_columns': reader.fieldnames,
        }), 400

    # Create an import batch record to track this upload
    try:
        batch = ImportBatch(
            filename=(getattr(file, 'filename', None) or None),
            uploader_id=str(get_jwt_identity() or get_jwt().get('sub') or 'unknown'),
            uploader_role=claims.get('role')
        )
        db.session.add(batch)
        db.session.flush()  # get batch.id
    except Exception as e:
        return jsonify({'message': 'Failed to create import batch', 'error': str(e)}), 500

    imported = 0
    skipped = 0
    errors = []
    created_ids = []

    for idx, row in enumerate(reader, start=2):
        # Basic presence checks using detected column names
        try:
            val_occurred = row.get(column_map.get('occurred_at'))
            val_severity = row.get(column_map.get('severity'))
            val_location = row.get(column_map.get('location'))
        except Exception:
            val_occurred = val_severity = val_location = None

        if not val_occurred or not val_severity or not val_location:
            skipped += 1
            errors.append({"row": idx, "reason": "Missing required field(s)"})
            continue

        # Parse datetime: accept ISO first, then common CSV formats, then fall
        # back to python-dateutil if available. This lets imports accept values
        # like '2015-10-22 at 06:07PM' which appear in provided CSVs.
        def _parse_occurred(s):
            if not s:
                raise ValueError('Empty occurred_at')
            # try ISO
            try:
                return datetime.fromisoformat(s)
            except Exception:
                pass
            # try common formats
            fmts = [
                "%Y-%m-%d at %I:%M%p",
                "%Y-%m-%d %I:%M%p",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y %I:%M%p",
            ]
            for f in fmts:
                try:
                    return datetime.strptime(s, f)
                except Exception:
                    continue
            # try dateutil if installed
            try:
                from dateutil import parser as _dp
                return _dp.parse(s)
            except Exception:
                raise ValueError(f"Invalid occurred_at: Invalid isoformat string: '{s}'")

        try:
            occurred_at = _parse_occurred(val_occurred)
        except Exception as e:
            skipped += 1
            errors.append({"row": idx, "reason": f"Invalid occurred_at: {str(e)}"})
            continue

        # Normalize and validate severity
        try:
            severity = val_severity.strip().lower()
        except Exception:
            severity = ''

        if severity not in ("low", "medium", "high"):
            skipped += 1
            errors.append({"row": idx, "reason": f"Invalid severity: {val_severity}"})
            continue

        # Everything OK -> create record
        try:
            # Normalize location: try to map to a Tunisian governorate if possible
            raw_loc = (val_location or '').strip()
            # simple mapping by substring match (case-insensitive)
            governorates = [
                'Ariana','Béja','Ben Arous','Bizerte','Gabès','Gafsa','Jendouba','Kairouan',
                'Kasserine','Kébili','Le Kef','Mahdia','Manouba','Medenine','Monastir','Nabeul',
                'Sfax','Sidi Bouzid','Siliana','Sousse','Tataouine','Tozeur','Tunis','Zaghouan'
            ]
            mapped = None
            low = raw_loc.lower()
            for g in governorates:
                if g.lower() in low:
                    mapped = g
                    break

            location_value = mapped if mapped else raw_loc

            # capture delegation if present in CSV
            delegation_val = None
            if column_map.get('delegation'):
                delegation_val = (row.get(column_map.get('delegation')) or '').strip() or None

            cause_val = None
            if column_map.get('cause'):
                cause_val = row.get(column_map.get('cause')) or None

            accident = Accident(
                occurred_at=occurred_at,
                severity=severity,
                location=location_value,
                governorate=(mapped if mapped else None),
                delegation=delegation_val,
                cause=(cause_val or None),
                source="government_import",
                batch_id=batch.id,
            )
            db.session.add(accident)
            db.session.flush()  # get id
            created_ids.append(accident.id)
            imported += 1
        except Exception as e:
            # Catch model/db errors for specific row
            skipped += 1
            errors.append({"row": idx, "reason": f"DB error: {str(e)}"})

    # Commit only once
    # Update batch counters and commit
    try:
        batch.imported_count = imported
        batch.skipped_count = skipped
        db.session.add(batch)
        db.session.commit()
    except Exception as e:
        # If commit fails, return an error with details
        db.session.rollback()
        return jsonify({
            "message": "Database commit failed",
            "error": str(e),
        }), 500
    # Audit log the import action
    try:
        actor = get_jwt_identity() or get_jwt().get('sub') or 'unknown'
        role = get_jwt().get('role')
        details = f"imported={imported},skipped={skipped},created_ids={created_ids}"
        logger.info(f"{actor} | {role} | import | {details}")
    except Exception:
        # Don't fail the request if logging fails
        pass

    return jsonify({
        "message": "Import completed",
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "created_ids": created_ids,
        "batch_id": batch.id,
        "column_map": column_map,
    }), 200


@import_api.route("", methods=["DELETE"])
@jwt_required()
def delete_imports():
    """Delete previously imported records from government_import source.

    Only users with role 'government' may call this.
    Returns the number of deleted records.
    """
    claims = get_jwt()
    if claims.get("role") != "government":
        return jsonify({"message": "Forbidden"}), 403

    # Optional batch_id to delete only one import batch
    batch_id = request.args.get('batch_id') or request.form.get('batch_id')
    try:
        if batch_id:
            try:
                bid = int(batch_id)
            except Exception:
                return jsonify({'message': 'Invalid batch_id'}), 400
            # delete accidents for that batch
            res = Accident.query.filter_by(batch_id=bid).delete(synchronize_session=False)
            # also delete the batch record itself
            ImportBatch.query.filter_by(id=bid).delete(synchronize_session=False)
        else:
            # Delete rows imported via government_import source
            res = Accident.query.filter_by(source="government_import").delete(synchronize_session=False)

        db.session.commit()
        # Audit log the deletion with actor info and count
        try:
            actor = get_jwt_identity() or claims.get('sub') or 'unknown'
            role = claims.get('role')
            logger.info(f"{actor} | {role} | delete_imports | batch_id={batch_id} deleted={res}")
        except Exception:
            pass
        return jsonify({"message": "Deleted imported records", "deleted": res, "batch_id": batch_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Deletion failed", "error": str(e)}), 500


@import_api.route("/batches", methods=["GET"])
@jwt_required()
def list_batches():
    """Return recent import batches for UI history."""
    claims = get_jwt()
    if claims.get('role') != 'government':
        return jsonify({'message': 'Forbidden'}), 403

    # return last 50 batches
    try:
        batches = ImportBatch.query.order_by(ImportBatch.created_at.desc()).limit(50).all()
        out = []
        for b in batches:
            out.append({
                'id': b.id,
                'filename': b.filename,
                'uploader_id': b.uploader_id,
                'uploader_role': b.uploader_role,
                'created_at': b.created_at.isoformat(),
                'imported_count': b.imported_count,
                'skipped_count': b.skipped_count,
            })
        return jsonify({'batches': out}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch batches', 'error': str(e)}), 500
