import os

from flask import Flask, jsonify
from flask_smorest import Api

from db import db
from blocklist import BLOCKLIST
from resources.item import item_blueprint as Item_Blueprint
from resources.store import store_blueprint as Store_Blueprint
from resources.tag import tag_blueprint as Tag_Blueprint
from resources.user import user_blueprint as User_Blueprint
from flask_jwt_extended import JWTManager


def create_app(db_url=None):
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores Rest API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # create using secrets.SystemRandom().getrandbits(128)
    app.config["JWT_SECRET_KEY"] = "320350877148003597330159706665228258272"
    db.init_app(app)

    api = Api(app)

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {
                    "description": "The token has been revoked",
                    "error": "token_revoked"
                }
            ), 401
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {
                    "message": "The token has expired.",
                    "error": "token_expired"
                }
            ), 401
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {
                    "message": "Signature verification failed.",
                    "error": "invalid_token"
                }
            ), 401
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "message": "Request does not contain an access token.",
                    "error": "authorization_required"
                }
            ), 401
        )

    @app.before_first_request
    def create_tables():
        db.create_all()

    api.register_blueprint(Store_Blueprint)
    api.register_blueprint(Item_Blueprint)
    api.register_blueprint(Tag_Blueprint)
    api.register_blueprint(User_Blueprint)

    return app
