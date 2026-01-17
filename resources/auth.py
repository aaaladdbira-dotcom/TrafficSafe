from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models.user import User
from schemas.user import UserRegisterSchema, UserLoginSchema, UserResponseSchema

blp = Blueprint(
    "Auth",
    "auth",
    url_prefix="/api/v1/auth",
    description="Authentication"
)


@blp.route("/register", methods=["POST"])
@blp.arguments(UserRegisterSchema)
@blp.response(201, UserResponseSchema)
def register_user(user_data):
    # Prevent government registration
    if user_data.get("user_type") == "government":
        abort(400, message="Cannot register as government user.")

    if User.query.filter_by(email=user_data["email"]).first():
        abort(409, message="Email already exists")
    if User.query.filter_by(national_id=user_data["national_id"]).first():
        abort(409, message="National ID already exists")

    # Validate required fields per user type
    from schemas.user import UserRegisterSchema
    UserRegisterSchema.validate(user_data)

    # Assign role based on user_type
    role = user_data["user_type"]

    user = User(
        full_name=user_data["full_name"],
        gender=user_data["gender"],
        date_of_birth=user_data["date_of_birth"],
        email=user_data["email"],
        password_hash=generate_password_hash(user_data["password"]),
        role=role,
        national_id=user_data["national_id"],
        user_type=user_data["user_type"],
        work_place=user_data.get("work_place"),
        badge_number=user_data.get("badge_number"),
        journalist_id=user_data.get("journalist_id"),
        avatar_url=user_data.get("avatar_url"),
    )

    db.session.add(user)
    db.session.commit()

    return user


@blp.route("/login", methods=["POST"])
@blp.arguments(UserLoginSchema)
def login_user(login_data):
    user = User.query.filter_by(email=login_data["email"]).first()

    if not user or not check_password_hash(user.password_hash, login_data["password"]):
        abort(401, message="Invalid credentials")

    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "user_type": user.user_type,
        },
    )

    return {
        "access_token": token,
        "role": user.role,
        "user_type": user.user_type,
    }
