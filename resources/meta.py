from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from flask import jsonify

blp = Blueprint("meta", "meta", url_prefix="/api/v1/meta")


@blp.route("/locations")
@jwt_required()
def locations():
    """Return canonical list of Tunisian governorates."""
    tunisia_states = [
        'Ariana','Béja','Ben Arous','Bizerte','Gabès','Gafsa','Jendouba','Kairouan',
        'Kasserine','Kébili','Le Kef','Mahdia','Manouba','Medenine','Monastir','Nabeul',
        'Sfax','Sidi Bouzid','Siliana','Sousse','Tataouine','Tozeur','Tunis','Zaghouan'
    ]
    return jsonify({"locations": tunisia_states})
