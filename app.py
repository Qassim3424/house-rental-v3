from flask import Flask, request, redirect, url_for, session, render_template

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "ca8b2f05e71fb8a8c17b91fba2ddd564c1b082c0b4f1220019443c561d2764e2"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///houses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



# =========================
# DATABASE
# =========================
from models import db, User, House, Appointment, Favorite
db.init_app(app)
@app.context_processor
def pending_appointments_count():

    count = 0

    if session.get("user_id"):

        count = Appointment.query.join(House).filter(
            House.owner_id == session["user_id"],
            Appointment.status == "pending"
        ).count()

    return dict(pending_count=count)

# HTML
# =========================

@app.route("/")
def home():

    q = request.args.get("q", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    location = request.args.get("location", "").strip()
    governorate = request.args.get("governorate", "").strip()

    query = House.query.filter_by(is_active=True)

    if q:
        query = query.filter(
            db.or_(
                House.title.ilike(f"%{q}%"),
                House.location.ilike(f"%{q}%"),
                House.description.ilike(f"%{q}%")
            )
        )

    if min_price.isdigit():
        query = query.filter(House.price >= int(min_price))

    if max_price.isdigit():
        query = query.filter(House.price <= int(max_price))

    if governorate:
        query = query.filter(
            House.governorate.ilike(f"%{governorate}%")
        )

    if location:
        query = query.filter(
            House.location.ilike(f"%{location}%")
        )

    houses = query.order_by(House.id.desc()).all()

    return render_template("home.html", houses=houses)


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        phone = request.form.get("phone", "").strip()
        phone = phone.replace(" ", "")
        phone = phone.replace("-", "")

        if phone.startswith("+964"):
                phone = phone[1:]

        elif phone.startswith("0"):
                phone = "964" + phone[1:]

        password = request.form.get("password", "")

        if not username or not password:
            error = "يرجى إدخال اسم المستخدم وكلمة المرور."

        elif len(password) < 6:
            error = "كلمة المرور يجب أن تكون 6 أحرف على الأقل."

        elif User.query.filter_by(username=username).first():
            error = "اسم المستخدم موجود مسبقًا."

        else:
            user = User(
                username=username,
                password=generate_password_hash(password),
                phone=phone or None
            )

            db.session.add(user)
            db.session.commit()

            session["user_id"] = user.id

            return redirect("/")

    return render_template("register.html", error=error)

# =========================
# APPOINTMENTS
# =========================

@app.route("/appointments")
def appointments():

    if not session.get("user_id"):
        return redirect("/login")

    appointments = Appointment.query.join(House).filter(
        House.owner_id == session["user_id"]
    ).order_by(Appointment.id.desc()).all()

    return render_template(
        "appointments.html",
        appointments=appointments
    )
@app.route("/favorite/<int:house_id>")
def add_favorite(house_id):

    if not session.get("user_id"):
        return redirect("/login")

    existing = Favorite.query.filter_by(
        user_id=session["user_id"],
        house_id=house_id
    ).first()

    if not existing:
        favorite = Favorite(
            user_id=session["user_id"],
            house_id=house_id
        )

        db.session.add(favorite)
        db.session.commit()

    return redirect("/house/" + str(house_id))
@app.route("/favorites")
def favorites():

    if not session.get("user_id"):
        return redirect("/login")

    favorites = Favorite.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "favorites.html",
        favorites=favorites
    )

@app.route("/my-appointments")
def my_appointments():

    if not session.get("user_id"):
        return redirect("/login")

    appointments = Appointment.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Appointment.id.desc()
    ).all()

    return render_template(
        "my_appointments.html",
        appointments=appointments
    )

@app.route("/appointment/<int:appointment_id>/<status>")
def update_appointment_status(appointment_id, status):

    if not session.get("user_id"):
        return redirect("/login")

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.house.owner_id != session["user_id"]:
        return redirect("/appointments")

    if status in ["approved", "rejected"]:
        appointment.status = status
        db.session.commit()

    return redirect("/appointments")

# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/")

        error = "اسم المستخدم أو كلمة المرور غير صحيحة."

    return render_template("login.html", error=error)


# =========================
# MY ACCOUNT
# =========================

@app.route("/account", methods=["GET", "POST"])
def account():

    if not session.get("user_id"):
        return redirect("/login")

    user = User.query.get_or_404(session["user_id"])
    message = None

    if request.method == "POST":

        phone = request.form.get("phone", "").strip()

        phone = phone.replace(" ", "")
        phone = phone.replace("-", "")

        if phone.startswith("+964"):
            phone = phone[1:]

        elif phone.startswith("0"):
            phone = "964" + phone[1:]

        user.phone = phone or None
        db.session.commit()

        message = "تم حفظ رقم الهاتف بنجاح ✅"

    return render_template(
        "account.html",
        user=user,
        message=message
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# MY HOUSES
# =========================

@app.route("/my-houses")
def my_houses():

    if not session.get("user_id"):
        return redirect("/login")

    houses = House.query.filter_by(
        owner_id=session["user_id"]
    ).order_by(House.id.desc()).all()

    return render_template(
        "my_houses.html",
        houses=houses
    )
@app.route("/toggle-house/<int:house_id>")
def toggle_house(house_id):

    if not session.get("user_id"):
        return redirect("/login")

    house = House.query.get_or_404(house_id)

    if house.owner_id != session["user_id"]:
        return redirect("/my-houses")

    house.is_active = not house.is_active

    db.session.commit()

    return redirect("/my-houses")

# =========================
# EDIT HOUSE
# =========================

@app.route("/edit-house/<int:house_id>", methods=["GET", "POST"])
def edit_house(house_id):

    if not session.get("user_id"):
        return redirect("/login")

    house = House.query.get_or_404(house_id)

    # المالك فقط يستطيع تعديل العقار
    if house.owner_id != session["user_id"]:
        return redirect("/my-houses")

    if request.method == "POST":

        house.title = request.form["title"]
        house.governorate = request.form["governorate"]
        house.location = request.form["location"]
        house.price = int(request.form["price"])
        house.status = request.form["status"]
        house.description = request.form.get("description", "")

        from werkzeug.utils import secure_filename
        import os
        import uuid

        upload_dir = os.path.join(app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # استبدال كل صورة بشكل مستقل
        # إذا لم يختار المستخدم صورة معينة، تبقى الصورة القديمة كما هي.

        for i in range(1, 4):

            image = request.files.get(f"image{i}")

            if image and image.filename:

                old_filename = getattr(house, f"image{i}")

                ext = os.path.splitext(image.filename)[1].lower()

                if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                       continue

                filename = secure_filename(str(uuid.uuid4()) + ext)

                image.save(
                    os.path.join(upload_dir, filename)
                )

                setattr(house, f"image{i}", filename)

                # حذف الصورة القديمة بعد نجاح حفظ الجديدة
                if old_filename:

                    old_path = os.path.join(
                        upload_dir,
                        old_filename
                    )

                    if os.path.isfile(old_path):
                        os.remove(old_path)

        # استبدال الفيديو إذا اختار فيديو جديد
        video = request.files.get("video")

        if video and video.filename:

            ext = os.path.splitext(video.filename)[1].lower()
            filename = secure_filename(str(uuid.uuid4()) + ext)

            video.save(
                os.path.join(upload_dir, filename)
            )

            house.video = filename

        db.session.commit()

        return redirect("/my-houses")

    return render_template(
        "edit_house.html",
        house=house
    )


# =========================
# DELETE HOUSE
# =========================

@app.route("/delete-house/<int:house_id>", methods=["POST"])
def delete_house(house_id):

    if not session.get("user_id"):
        return redirect("/login")

    house = House.query.get_or_404(house_id)

    # المالك فقط يستطيع حذف العقار
    if house.owner_id != session["user_id"]:
        return redirect("/my-houses")

    import os

    upload_dir = os.path.join(app.root_path, "uploads")

    # حذف الصور المرتبطة بالعقار
    for image_name in [
        house.image1,
        house.image2,
        house.image3
    ]:

        if image_name:
            image_path = os.path.join(upload_dir, image_name)

            if os.path.isfile(image_path):
                os.remove(image_path)

    # حذف الفيديو
    if house.video:

        video_path = os.path.join(
            upload_dir,
            house.video
        )

        if os.path.isfile(video_path):
            os.remove(video_path)

    # حذف المواعيد المرتبطة بالعقار
    appointments = Appointment.query.filter_by(
        house_id=house.id
    ).all()

    for appointment in appointments:
        db.session.delete(appointment)

    # حذف المفضلات المرتبطة بالعقار
    favorites = Favorite.query.filter_by(
        house_id=house.id
    ).all()

    for favorite in favorites:
        db.session.delete(favorite)

    # حذف العقار
    db.session.delete(house)
    db.session.commit()

    return redirect("/my-houses")



# =========================
# ADD HOUSE
# =========================

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory("uploads", filename)

@app.route("/house/<int:house_id>")
def house_detail(house_id):
    house = House.query.get_or_404(house_id)
    return render_template("house_detail.html", house=house)

@app.route("/add-house", methods=["GET", "POST"])
def add_house():

    if not session.get("user_id"):
        return redirect("/login")

    if request.method == "POST":

        house = House(
            title=request.form["title"],
            governorate=request.form["governorate"],
            location=request.form["location"],
            price=int(request.form["price"]),
            description=request.form.get("description", ""),
            owner_id=session["user_id"]
        )

        from werkzeug.utils import secure_filename
        import os
        import uuid

        upload_dir = os.path.join(app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        images = request.files.getlist("images")

        for i, image in enumerate(images[:3], start=1):

            if image and image.filename:

                ext = os.path.splitext(image.filename)[1].lower()
                if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                    continue

                filename = secure_filename(str(uuid.uuid4()) + ext)

                image.save(
                    os.path.join(upload_dir, filename)
                )

                setattr(
                    house,
                    f"image{i}",
                    filename
                )

        video = request.files.get("video")

        if video and video.filename:

            ext = os.path.splitext(video.filename)[1].lower()
            if ext not in [".mp4", ".mov", ".avi"]:
                  return "نوع الفيديو غير مسموح"

            filename = secure_filename(str(uuid.uuid4()) + ext)

            video.save(
                os.path.join(upload_dir, filename)
            )

            house.video = filename

        db.session.add(house)
        db.session.commit()

        return redirect("/")

    return render_template(
        "add_house.html"
    )
# =========================
# BOOK APPOINTMENT
# =========================

@app.route("/book-appointment/<int:house_id>", methods=["GET", "POST"])
def book_appointment(house_id):

    if not session.get("user_id"):
        return redirect("/login")

    house = House.query.get_or_404(house_id)

    if request.method == "POST":

        appointment = Appointment(
            user_id=session["user_id"],
            house_id=house.id,
            date=request.form["date"],
            time=request.form["time"],
            note=request.form.get("note", "")
        )

        db.session.add(appointment)
        db.session.commit()

        return redirect("/house/" + str(house.id))

    return render_template(
        "book_appointment.html",
        house=house
    )

# =========================
# DATABASE
# =========================

with app.app_context():

    db.create_all()


# =========================
# RUN
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )



