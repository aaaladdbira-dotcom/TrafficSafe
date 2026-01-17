from marshmallow import Schema, fields, validate

SEVERITY_VALUES = ["Low", "Medium", "High"]
REPORTER_VALUES = ["citizen", "police", "insurance", "media"]
WEATHER_VALUES = ["clear", "rain", "fog", "storm", "snow", "unknown"]
ROAD_VALUES = ["good", "damaged", "slippery", "construction", "unknown"]
STATUS_VALUES = ["reported", "validated", "resolved", "rejected"]

class AccidentCreateSchema(Schema):
    location = fields.String(required=True, validate=validate.Length(min=2))
    zone = fields.String(required=True, validate=validate.Length(min=2))

    speeding = fields.Boolean(load_default=False)
    phone_usage = fields.Boolean(load_default=False)
    drunk_driving = fields.Boolean(load_default=False)

    weather_condition = fields.String(load_default="unknown", validate=validate.OneOf(WEATHER_VALUES))
    road_condition = fields.String(load_default="unknown", validate=validate.OneOf(ROAD_VALUES))

    severity = fields.String(required=True, validate=validate.OneOf(SEVERITY_VALUES))
    injuries = fields.Integer(load_default=0, validate=validate.Range(min=0))
    fatalities = fields.Integer(load_default=0, validate=validate.Range(min=0))

    reported_by = fields.String(required=True, validate=validate.OneOf(REPORTER_VALUES))

class AccidentStatusUpdateSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(STATUS_VALUES))

class AccidentResponseSchema(AccidentCreateSchema):
    id = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
