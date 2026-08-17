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

    owner = db.relationship(
        "User",
        backref="houses"
    )
