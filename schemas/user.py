from marshmallow import Schema, fields, validate


class UserRegisterSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    gender = fields.String(required=True, validate=validate.OneOf(["male", "female", "other"]))
    date_of_birth = fields.Date(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    user_type = fields.String(
        required=True,
        validate=validate.OneOf(["police", "media", "citizen"]),
    )
    national_id = fields.String(
        required=True,
        validate=[validate.Regexp(r"^\d{8}$", error="National ID must be exactly 8 digits")],
    )
    work_place = fields.String()
    badge_number = fields.String()
    journalist_id = fields.String()

    @staticmethod
    def validate_fields(data, **kwargs):
        user_type = data.get("user_type")
        errors = {}
        if user_type == "police":
            if not data.get("work_place"):
                errors["work_place"] = ["Place of work is required for police."]
            if not data.get("badge_number"):
                errors["badge_number"] = ["Badge number is required for police."]
        elif user_type == "media":
            if not data.get("work_place"):
                errors["work_place"] = ["Place of work is required for media."]
            if not data.get("journalist_id"):
                errors["journalist_id"] = ["Journalist ID is required for media."]
        return errors

    @classmethod
    def validate(cls, data, **kwargs):
        errors = cls.validate_fields(data, **kwargs)
        if errors:
            raise validate.ValidationError(errors)
        return data


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class UserResponseSchema(Schema):
    full_name = fields.String()
    gender = fields.String()
    date_of_birth = fields.Date()
    age = fields.Method("get_age")

    def get_age(self, obj):
        return obj.age if hasattr(obj, "age") else None
    id = fields.Int()
    email = fields.Email()
    role = fields.String()
    user_type = fields.String()
    national_id = fields.String()
    work_place = fields.String(allow_none=True)
    badge_number = fields.String(allow_none=True)
    journalist_id = fields.String(allow_none=True)
