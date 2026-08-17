from flask import Flask, request, redirect, url_for, session, render_template_string, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "v3-house-rental-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///houses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# DATABASE
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)


class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    location = db.Column(db.String(200), nullable=False)

    price = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text)

    image1 = db.Column(db.String(500))
    image2 = db.Column(db.String(500))
    image3 = db.Column(db.String(500))
    video = db.Column(db.String(500))

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    owner = db.relationship("User", backref="houses")


# =========================
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

    houses = House.query.order_by(House.id.desc()).all()

    return render_template("home.html", houses=houses)


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()

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
                password=generate_password_hash(password)
            )

            db.session.add(user)

            db.session.commit()

            session["user_id"] = user.id

            return redirect("/")


    return render_template_string(
        STYLE + """

        <header>
            <h1>إنشاء حساب</h1>
        </header>

        <div class="container">

            <div class="card">

                {% if error %}
                    <div class="error">
                        {{ error }}
                    </div>
                {% endif %}

                <form method="POST">

                    <input
                        name="username"
                        placeholder="اسم المستخدم"
                        required
                    >

                    <input
                        name="password"
                        type="password"
                        placeholder="كلمة المرور"
                        required
                    >

                    <button>
                        إنشاء الحساب
                    </button>

                </form>

                <p>
                    لديك حساب؟
                    <a href="/login">تسجيل الدخول</a>
                </p>

            </div>

        </div>
        """,
        error=error
    )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()

        password = request.form.get("password", "")

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id

            return redirect("/")

        error = "اسم المستخدم أو كلمة المرور غير صحيحة."


    return render_template_string(
        STYLE + """

        <header>
            <h1>تسجيل الدخول</h1>
        </header>

        <div class="container">

            <div class="card">

                {% if error %}
                    <div class="error">
                        {{ error }}
                    </div>
                {% endif %}

                <form method="POST">

                    <input
                        name="username"
                        placeholder="اسم المستخدم"
                        required
                    >

                    <input
                        name="password"
                        type="password"
                        placeholder="كلمة المرور"
                        required
                    >

                    <button>
                        دخول
                    </button>

                </form>

                <p>
                    ليس لديك حساب؟
                    <a href="/register">
                        إنشاء حساب
                    </a>
                </p>

            </div>

        </div>
        """,
        error=error
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# ADD HOUSE
# =========================

@app.route("/add-house", methods=["GET", "POST"])
def add_house():

    if not session.get("user_id"):

        return redirect("/login")


    if request.method == "POST":

        house = House(

            title=request.form["title"],

            location=request.form["location"],

            price=int(request.form["price"]),

            description=request.form.get("description", ""),

            owner_id=session["user_id"]

        )

        db.session.add(house)

        db.session.commit()

        return redirect("/")


    return render_template_string(
        STYLE + """

        <header>
            <h1>🏠 إضافة بيت</h1>
        </header>

        <div class="container">

            <div class="card">

                <form method="POST">

                    <input
                        name="title"
                        placeholder="عنوان البيت"
                        required
                    >

                    <input
                        name="location"
                        placeholder="الموقع"
                        required
                    >

                    <input
                        name="price"
                        type="number"
                        placeholder="السعر الشهري بالدينار"
                        required
                    >

                    <textarea
                        name="description"
                        rows="5"
                        placeholder="وصف البيت"
                    ></textarea>

                    <button>
                        نشر البيت
                    </button>

                </form>

            </div>

        </div>
        """
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
