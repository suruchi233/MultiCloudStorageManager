import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)
from flask_bcrypt import Bcrypt
import sqlite3
import os
from werkzeug.utils import secure_filename
from services.aws_service import generate_download_url
from services.db_service import (
    save_file,
    get_user_files,
    search_user_files,
    get_file_owner,
    delete_file_record,
    get_cloud_provider
)
from services.aws_service import (
    upload_file,
    list_files,
    delete_file,
    download_file
)
from services.gcp_service import (
    upload_file_gcp,
    download_file_gcp,
    delete_file_gcp
)
from services.encryption_service import (
    encrypt_file,
    decrypt_file
)
ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "docx",
    "xlsx",
    "txt"
}
app = Flask(__name__)



app.secret_key = os.getenv("SECRET_KEY", "multicloud_secret_key")

bcrypt = Bcrypt(app)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (username,email,password) VALUES (?,?,?)",
                (username, email, hashed_password),
            )

            conn.commit()

            flash("Registration Successful")

            return redirect(url_for("login_page"))

        except:

            flash("Email already exists")

        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (email,),
    ).fetchone()

    conn.close()

    if user:
        print("User found:", user["email"])

        if bcrypt.check_password_hash(user["password"], password):
            print("Password matched")

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))
        else:
            print("Password did NOT match")
    else:
        print("User not found")

    flash("Invalid Email or Password")

    return redirect(url_for("login_page"))

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    search = request.args.get("search", "")

    if search:
        files = search_user_files(
            session["user_id"],
            search
        )
    else:
        files = get_user_files(
            session["user_id"]
        )

    total = len(files)

    aws_files = len([f for f in files if f[3] == "AWS"])
    gcp_files = len([f for f in files if f[3] == "GCP"])

    if total == 0:
        aws_percent = 0
        gcp_percent = 0
    else:
        aws_percent = round((aws_files / total) * 100)
        gcp_percent = round((gcp_files / total) * 100)
    
    return render_template(
    "dashboard.html",
    username=session["username"],
    files=files,
    search=search,
    total_files=total,
    aws_files=aws_files,
    gcp_files=gcp_files,
    encrypted_files=total,
    aws_percent=aws_percent,
    gcp_percent=gcp_percent
)

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login_page"))

@app.route("/upload", methods=["POST"])
def upload():

    if "user_id" not in session:
        return redirect("/")

    if "file" not in request.files:
        flash("No File Selected")
        return redirect("/dashboard")

    file = request.files["file"]

    if file.filename == "":
        flash("No File Selected")
        return redirect("/dashboard")

    if not allowed_file(file.filename):
        flash("File type not allowed")
        return redirect("/dashboard")
    cloud_provider = request.form["cloud"]
    filename = secure_filename(file.filename)

    upload_folder = os.path.join(
    os.getcwd(),
    "uploads"
    )

    os.makedirs(
    upload_folder,
    exist_ok=True
    )

    filepath = os.path.join(
    upload_folder,
    filename
    )

    file.save(filepath)

    # Get the file size AFTER saving the file
    file_size = os.path.getsize(filepath)
    
    encrypt_file(filepath)

    success = False

    if cloud_provider == "AWS":
        success = upload_file(filepath, filename)

    elif cloud_provider == "GCP":
        success = upload_file_gcp(filepath, filename)

    print("Upload success:", success)
    save_file(
    session["user_id"],
    filename,
    cloud_provider,
    file_size
)
    os.remove(filepath)

    flash("File Uploaded Successfully")

    return redirect("/dashboard")
@app.route("/delete/<filename>")
def delete(filename):

    if "user_id" not in session:
        return redirect("/")

    owner = get_file_owner(filename)

    if owner is None:
        flash("File not found")
        return redirect("/dashboard")

    if owner[0] != session["user_id"]:
        flash("Access Denied")
        return redirect("/dashboard")

    cloud = get_cloud_provider(filename)

    if cloud[0] == "AWS":
        delete_file(filename)

    elif cloud[0] == "GCP":
        delete_file_gcp(filename)
        
    delete_file_record(filename)

    flash("File Deleted Successfully")

    return redirect("/dashboard")

@app.route("/download/<filename>")
def download(filename):

    if "user_id" not in session:
        return redirect("/")

    owner = get_file_owner(filename)

    if owner is None:
        flash("File not found")
        return redirect("/dashboard")

    if owner[0] != session["user_id"]:
        flash("Access Denied")
        return redirect("/dashboard")

    temp_folder = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_folder, exist_ok=True)

    temp_path = os.path.join(temp_folder, filename)

    cloud = get_cloud_provider(filename)

    if cloud[0] == "AWS":
        download_file(filename, temp_path)

    elif cloud[0] == "GCP":
        download_file_gcp(filename, temp_path)

    # Debug before decryption
    with open(temp_path, "rb") as f:
        print("Before decrypt:", f.read(30))

    decrypt_file(temp_path)

    # Debug after decryption
    with open(temp_path, "rb") as f:
        print("After decrypt:", f.read(30))

    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename
    )
if __name__ == "__main__":
    app.run(debug=True)