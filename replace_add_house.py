from pathlib import Path

p = Path("app.py")
s = p.read_text()

start = s.index('@app.route("/add-house"')
end = s.index('# =========================\n# DATABASE', start)

new = '''@app.route("/add-house", methods=["GET", "POST"])
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


'''

p.write_text(s[:start] + new + s[end:])
print("ADD_HOUSE_FIXED")
