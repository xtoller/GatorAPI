from flask.views import MethodView
from flask_smorest import abort, Blueprint
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema

item_blueprint = Blueprint("Items", __name__, description="Items Operation(s)")


@item_blueprint.route("/item")
class ItemList(MethodView):
    @jwt_required()
    @item_blueprint.response(200, ItemSchema(many=True))
    def get(self):
        item = ItemModel.query.all()
        return item

    @jwt_required(fresh=True)
    @item_blueprint.arguments(ItemSchema)
    @item_blueprint.response(201, ItemSchema)
    def post(self, item_data):
        item = ItemModel(**item_data)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting item to database")
        return item


@item_blueprint.route("/item/<int:item_id>")
class Item(MethodView):
    @jwt_required()
    @item_blueprint.response(200, ItemSchema)
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item

    @jwt_required()
    @item_blueprint.arguments(ItemUpdateSchema)
    @item_blueprint.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get(item_id)
        if item:
            item.prise = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemModel(item_id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()

        return item

    @jwt_required()
    def delete(self, item_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted"}
