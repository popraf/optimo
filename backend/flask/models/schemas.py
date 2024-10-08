from marshmallow import Schema, fields


class ReservationSchema(Schema):
    book_id = fields.Integer(required=True)


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


reservation_schema = ReservationSchema()
login_schema = LoginSchema()
