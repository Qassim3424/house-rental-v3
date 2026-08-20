from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    phone = db.Column(
        db.String(30)
    )


class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    governorate = db.Column(
        db.String(100)
    )

    location = db.Column(
        db.String(200),
        nullable=False
    )

    price = db.Column(
        db.Integer,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    image1 = db.Column(
        db.String(500)
    )

    image2 = db.Column(
        db.String(500)
    )

    image3 = db.Column(
        db.String(500)
    )

    video = db.Column(
        db.String(500)
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    is_active = db.Column(
    db.Boolean,
    default=True,
    nullable=False

    )

    status = db.Column(
        db.String(20),
        default="available",
        nullable=False
    )

    owner = db.relationship(
        "User",
        backref="houses"
    )

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    house_id = db.Column(
        db.Integer,
        db.ForeignKey("house.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="favorites"
    )

    house = db.relationship(
        "House",
        backref="favorited_by"
    )

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    house_id = db.Column(
        db.Integer,
        db.ForeignKey("house.id"),
        nullable=False
    )

    date = db.Column(
        db.String(20),
        nullable=False
    )

    time = db.Column(
        db.String(20),
        nullable=False
    )

    note = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="appointments"
    )

    house = db.relationship(
        "House",
        backref="appointments"
    )
