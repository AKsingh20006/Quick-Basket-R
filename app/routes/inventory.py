import os
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import ProductForm
from app.models import Product
from app.services.excel_service import sync_products_to_excel

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


def _sync_products():
    sync_products_to_excel(current_app.config["PRODUCTS_EXCEL"])


def _save_product_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file_storage.filename)
    _, extension = os.path.splitext(filename)
    stored_filename = f"{uuid4().hex}{extension.lower()}"
    file_storage.save(os.path.join(upload_folder, stored_filename))
    return stored_filename


def _populate_product(product, form):
    product.name = form.name.data.strip()
    product.barcode = form.barcode.data.strip() if form.barcode.data else None
    product.category = form.category.data.strip()
    product.quantity = form.quantity.data
    product.low_stock_threshold = form.low_stock_threshold.data
    product.buying_price = form.buying_price.data
    product.selling_price = form.selling_price.data
    product.expiry_date = form.expiry_date.data
    product.supplier = form.supplier.data.strip() if form.supplier.data else None

    image_filename = _save_product_image(form.image.data)
    if image_filename:
        product.image_filename = image_filename


@inventory_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Product.query
    if search:
        like_search = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(like_search),
                Product.barcode.ilike(like_search),
                Product.supplier.ilike(like_search),
            )
        )
    if category:
        query = query.filter(Product.category == category)

    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False,
    )
    categories = [
        row[0]
        for row in db.session.query(Product.category)
        .filter(Product.category.isnot(None))
        .distinct()
        .order_by(Product.category.asc())
        .all()
    ]

    return render_template(
        "inventory.html",
        title="Inventory",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        search=search,
        selected_category=category,
    )


@inventory_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        if form.barcode.data and Product.query.filter_by(barcode=form.barcode.data.strip()).first():
            flash("A product with this barcode already exists.", "warning")
            return render_template("add_product.html", title="Add Product", form=form)

        product = Product()
        _populate_product(product, form)
        db.session.add(product)
        db.session.commit()
        _sync_products()

        flash("Product added successfully.", "success")
        return redirect(url_for("inventory.index"))

    return render_template("add_product.html", title="Add Product", form=form)


@inventory_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        if form.barcode.data:
            duplicate = Product.query.filter(
                Product.barcode == form.barcode.data.strip(),
                Product.id != product.id,
            ).first()
            if duplicate:
                flash("Another product already uses this barcode.", "warning")
                return render_template("edit_product.html", title="Edit Product", form=form, product=product)

        _populate_product(product, form)
        db.session.commit()
        _sync_products()

        flash("Product updated successfully.", "success")
        return redirect(url_for("inventory.index"))

    return render_template("edit_product.html", title="Edit Product", form=form, product=product)


@inventory_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    try:
        db.session.delete(product)
        db.session.commit()

        _sync_products()

        flash("Product deleted successfully.", "success")

    except IntegrityError:
        db.session.rollback()

        flash(
            "This product cannot be deleted because it has already been used in previous sales.",
            "warning"
        )

    except Exception as e:
        db.session.rollback()

        flash(
            f"An unexpected error occurred: {str(e)}",
            "danger"
        )

    return redirect(url_for("inventory.index"))
