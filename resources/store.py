from flask.views import MethodView
from flask_smorest import abort, Blueprint
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from db import db
from models import StoreModel
from schemas import StoreSchema

store_blueprint = Blueprint("Stores", __name__, description="Stores Operation(s)")


@store_blueprint.route("/store/<int:store_id>")
class Store(MethodView):
    @jwt_required()
    @store_blueprint.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    @jwt_required()
    def delete(self, store_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted"}


@store_blueprint.route("/store")
class StoreList(MethodView):
    @jwt_required()
    @store_blueprint.response(200, StoreSchema(many=True))
    def get(self):
        store = StoreModel.query.all()
        return store

    @jwt_required()
    @store_blueprint.arguments(StoreSchema)
    @store_blueprint.response(200, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A store with that name already exist.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting item to database")
        return store
