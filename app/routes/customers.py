from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Customer, Sale

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


@customers_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()

    query = Customer.query
    if search:
        like_search = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like_search),
                Customer.phone.ilike(like_search),
                Customer.email.ilike(like_search),
            )
        )

    customers = query.order_by(Customer.name.asc()).all()
    customer_ids = [customer.id for customer in customers]
    spend_by_customer = {}
    if customer_ids:
        rows = (
            db.session.query(Sale.customer_id, db.func.coalesce(db.func.sum(Sale.total_amount), 0))
            .filter(Sale.customer_id.in_(customer_ids))
            .group_by(Sale.customer_id)
            .all()
        )
        spend_by_customer = {row[0]: float(row[1] or 0) for row in rows}

    return render_template(
        "customers.html",
        title="Customers",
        customers=customers,
        search=search,
        spend_by_customer=spend_by_customer,
    )


@customers_bp.route("/add", methods=["POST"])
@login_required
def add_customer():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip() or None
    email = (request.form.get("email") or "").strip() or None
    address = (request.form.get("address") or "").strip() or None

    if not name:
        flash("Customer name is required.", "warning")
        return redirect(url_for("customers.index"))

    db.session.add(Customer(name=name, phone=phone, email=email, address=address))
    db.session.commit()
    flash("Customer added successfully.", "success")
    return redirect(url_for("customers.index"))


@customers_bp.route("/<int:customer_id>/edit", methods=["POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.name = (request.form.get("name") or customer.name).strip()
    customer.phone = (request.form.get("phone") or "").strip() or None
    customer.email = (request.form.get("email") or "").strip() or None
    customer.address = (request.form.get("address") or "").strip() or None
    db.session.commit()
    flash("Customer updated successfully.", "success")
    return redirect(url_for("customers.index"))


@customers_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if customer.sales:
        flash("This customer has sales history and cannot be deleted.", "warning")
        return redirect(url_for("customers.index"))

    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully.", "info")
    return redirect(url_for("customers.index"))
