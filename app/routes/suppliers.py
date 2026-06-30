from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Supplier

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


@suppliers_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()

    query = Supplier.query
    if search:
        like_search = f"%{search}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(like_search),
                Supplier.phone.ilike(like_search),
                Supplier.email.ilike(like_search),
            )
        )

    suppliers = query.order_by(Supplier.name.asc()).all()
    return render_template("suppliers.html", title="Suppliers", suppliers=suppliers, search=search)


@suppliers_bp.route("/add", methods=["POST"])
@login_required
def add_supplier():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip() or None
    email = (request.form.get("email") or "").strip() or None
    address = (request.form.get("address") or "").strip() or None
    notes = (request.form.get("notes") or "").strip() or None

    if not name:
        flash("Supplier name is required.", "warning")
        return redirect(url_for("suppliers.index"))

    db.session.add(Supplier(name=name, phone=phone, email=email, address=address, notes=notes))
    db.session.commit()
    flash("Supplier added successfully.", "success")
    return redirect(url_for("suppliers.index"))


@suppliers_bp.route("/<int:supplier_id>/edit", methods=["POST"])
@login_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.name = (request.form.get("name") or supplier.name).strip()
    supplier.phone = (request.form.get("phone") or "").strip() or None
    supplier.email = (request.form.get("email") or "").strip() or None
    supplier.address = (request.form.get("address") or "").strip() or None
    supplier.notes = (request.form.get("notes") or "").strip() or None
    db.session.commit()
    flash("Supplier updated successfully.", "success")
    return redirect(url_for("suppliers.index"))


@suppliers_bp.route("/<int:supplier_id>/delete", methods=["POST"])
@login_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    flash("Supplier deleted successfully.", "info")
    return redirect(url_for("suppliers.index"))
