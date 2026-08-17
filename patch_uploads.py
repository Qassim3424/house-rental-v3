from pathlib import Path

p = Path("app.py")
s = p.read_text()

old = '''        house = House(
            title=request.form["title"],
            location=request.form["location"],
            price=int(request.form["price"]),
            description=request.form.get("description", ""),
            owner_id=session["user_id"]
        )
'''

new = '''        from werkzeug.utils import secure_filename
        import os
        import uuid

        upload_dir = os.path.join(app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        house = House(
            title=request.form["title"],
            location=request.form["location"],
            price=int(request.form["price"]),
            description=request.form.get("description", ""),
            owner_id=session["user_id"]
        )

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
'''

if old not in s:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(s.replace(old, new))
print("PATCH_OK")
