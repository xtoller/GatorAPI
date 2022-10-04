from flask.views import MethodView
from flask_smorest import abort, Blueprint
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

tag_blueprint = Blueprint("Tags", "tags", description="Tag Operation(s)")


@tag_blueprint.route("/store/<string:store_id>/tag")
class TagsInStore(MethodView):
    @jwt_required()
    @tag_blueprint.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @jwt_required()
    @tag_blueprint.arguments(TagSchema)
    @tag_blueprint.response(201, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
            abort(400, message=f"A tag with that name already applied")
        tag = TagModel(**tag_data, store_id=store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return tag


@tag_blueprint.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagToItem(MethodView):
    @jwt_required()
    @tag_blueprint.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag")
        return tag

    @jwt_required()
    @tag_blueprint.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag")
        return {"message": "Item removed from tag.", "item": item, "tag": tag}


@tag_blueprint.route("/tag/<int:tag_id>")
class Tag(MethodView):

    @jwt_required()
    @tag_blueprint.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @jwt_required()
    @tag_blueprint.response(202, description="Deletes a tag if no item is tagged with it")
    @tag_blueprint.alt_response(404, description="Tag not found")
    @tag_blueprint.alt_response(400, description="Returned if the tag is assigned to one or more items. "
                                                 "In this case the tag is not deleted.")
    def delete(self, tag_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted"}
        abort(
            400,
            message="Could not delete tag. Make sure tag is not associated with any item(s), then try again."
        )
