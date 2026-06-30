import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import StoreSettings
from app.services.backup_service import backup_database, restore_database
from app.services.excel_service import sync_products_to_excel, sync_sales_to_excel

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def index():
    return render_template("settings.html", title="Settings", settings=StoreSettings.get_solo())


@settings_bp.route("/store", methods=["POST"])
@login_required
def update_store():
    settings = StoreSettings.get_solo()
    settings.store_name = (request.form.get("store_name") or settings.store_name).strip()
    settings.owner_name = (request.form.get("owner_name") or "").strip() or None
    settings.phone = (request.form.get("phone") or "").strip() or None
    settings.email = (request.form.get("email") or "").strip() or None
    settings.currency = (request.form.get("currency") or settings.currency).strip()
    settings.theme = (request.form.get("theme") or settings.theme).strip()
    db.session.commit()
    flash("Store settings updated successfully.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def update_password():
    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
    elif len(new_password) < 8:
        flash("New password must be at least 8 characters.", "warning")
    elif new_password != confirm_password:
        flash("New password and confirmation do not match.", "warning")
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")

    return redirect(url_for("settings.index"))


@settings_bp.route("/backup", methods=["POST"])
@login_required
def backup():
    backup_path = backup_database(current_app.config.get("DB_PATH"), current_app.config["BACKUP_FOLDER"])
    if not backup_path:
        flash("Backup is only available for the local SQLite database.", "warning")
        return redirect(url_for("settings.index"))

    return send_file(backup_path, as_attachment=True, download_name=os.path.basename(backup_path))


@settings_bp.route("/restore", methods=["POST"])
@login_required
def restore():
    uploaded_file = request.files.get("backup_file")
    if not uploaded_file or not uploaded_file.filename:
        flash("Choose a backup (.db) file to restore.", "warning")
        return redirect(url_for("settings.index"))

    if not secure_filename(uploaded_file.filename).endswith(".db"):
        flash("Only .db backup files can be restored.", "warning")
        return redirect(url_for("settings.index"))

    temp_path = os.path.join(current_app.config["BACKUP_FOLDER"], "restore-upload.db")
    os.makedirs(current_app.config["BACKUP_FOLDER"], exist_ok=True)
    uploaded_file.save(temp_path)

    try:
        restore_database(current_app.config.get("DB_PATH"), temp_path)
    except ValueError as error:
        flash(str(error), "danger")
    else:
        flash("Database restored successfully. Please restart the application.", "success")

    return redirect(url_for("settings.index"))


@settings_bp.route("/export/products")
@login_required
def export_products():
    sync_products_to_excel(current_app.config["PRODUCTS_EXCEL"])
    return send_file(current_app.config["PRODUCTS_EXCEL"], as_attachment=True, download_name="products.xlsx")


@settings_bp.route("/export/sales")
@login_required
def export_sales():
    sync_sales_to_excel(current_app.config["SALES_EXCEL"])
    return send_file(current_app.config["SALES_EXCEL"], as_attachment=True, download_name="sales.xlsx")
