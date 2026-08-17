from flask import Flask, request, redirect, url_for, session, render_template_string, render_template

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "v3-house-rental-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///houses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



# =========================
# DATABASE
# =========================
from models import db, User, House

db.init_app(app)

# HTML
# =========================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    direction: rtl;
}

header {
    background: #111827;
    color: white;
    padding: 18px;
    text-align: center;
}

.container {
    max-width: 900px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 20px;
    margin: 15px 0;
    border-radius: 15px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08);
}

input,
textarea,
button {
    width: 100%;
    padding: 13px;
    margin-top: 10px;
    border-radius: 8px;
    border: 1px solid #ddd;
    font-size: 16px;
}

button {
    background: #111827;
    color: white;
    cursor: pointer;
}

button:hover {
    opacity: .9;
}

a {
    text-decoration: none;
}

.nav {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
}

.nav a {
    color: white;
}

.house {
    border-right: 5px solid #111827;
}

.price {
    font-size: 20px;
    font-weight: bold;
}

.error {
    background: #fee2e2;
    padding: 12px;
    border-radius: 8px;
}

.success {
    background: #dcfce7;
    padding: 12px;
    border-radius: 8px;
}

</style>
"""


# =========================
# HOME
# =========================

@app.route("/")
def home():

    q = request.args.get("q", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    location = request.args.get("location", "").strip()
    governorate = request.args.get("governorate", "").strip()

    query = House.query

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

    # حذف العقار من قاعدة البيانات
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
                filename = secure_filename(str(uuid.uuid4()) + ext)
                image.save(os.path.join(upload_dir, filename))
                setattr(house, f"image{i}", filename)

        video = request.files.get("video")

        if video and video.filename:
            ext = os.path.splitext(video.filename)[1].lower()
            filename = secure_filename(str(uuid.uuid4()) + ext)
            video.save(os.path.join(upload_dir, filename))
            house.video = filename

        db.session.add(house)
        db.session.commit()
        return redirect("/")

    return render_template("add_house.html")


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
