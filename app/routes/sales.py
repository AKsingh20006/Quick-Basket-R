from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO

from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func

from app.extensions import db
from app.models import Customer, Product, Sale, SaleItem
from app.services.excel_service import sync_products_to_excel, sync_sales_to_excel

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


def _money(value):
    try:
        return Decimal(str(value or "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def _next_invoice_number():
    return f"QB-{date.today().strftime('%Y%m%d')}-{(Sale.query.count() + 1):05d}"


def _sales_chart():
    today = date.today()
    start_date = today - timedelta(days=6)
    rows = (
        db.session.query(func.date(Sale.created_at), func.coalesce(func.sum(Sale.total_amount), 0))
        .filter(func.date(Sale.created_at) >= start_date.isoformat())
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at))
        .all()
    )
    values_by_date = {row[0]: float(row[1] or 0) for row in rows}
    labels = [(today - timedelta(days=offset)).strftime("%d %b") for offset in range(6, -1, -1)]
    values = [
        values_by_date.get((today - timedelta(days=offset)).isoformat(), 0)
        for offset in range(6, -1, -1)
    ]
    return labels, values


def _build_cart_items():
    product_ids = request.form.getlist("product_id[]")
    quantities = request.form.getlist("quantity[]")
    cart_items = []

    for raw_product_id, raw_quantity in zip(product_ids, quantities):
        if not raw_product_id:
            continue

        product = Product.query.get(int(raw_product_id))
        quantity = int(raw_quantity or 0)
        if not product or quantity <= 0:
            continue
        if quantity > product.quantity:
            raise ValueError(f"{product.name} has only {product.quantity} in stock.")

        line_total = _money(product.selling_price) * quantity
        cart_items.append((product, quantity, line_total))

    if not cart_items:
        raise ValueError("Add at least one product to the cart.")
    return cart_items


def _resolve_customer():
    customer_id = request.form.get("customer_id", type=int)
    if customer_id:
        customer = Customer.query.get(customer_id)
        if customer:
            return customer, customer.name, customer.phone

    name = (request.form.get("customer_name") or "").strip() or "Walk-in Customer"
    phone = (request.form.get("customer_phone") or "").strip() or None
    customer = None
    if name != "Walk-in Customer" or phone:
        customer = Customer(name=name, phone=phone)
        db.session.add(customer)
        db.session.flush()
    return customer, name, phone


def _create_sale():
    cart_items = _build_cart_items()
    customer, customer_name, customer_phone = _resolve_customer()
    discount = _money(request.form.get("discount_amount"))
    gst_percent = _money(request.form.get("gst_percent"))
    payment_method = (request.form.get("payment_method") or "Cash").strip()

    subtotal = sum((line_total for _, _, line_total in cart_items), Decimal("0.00"))
    if discount > subtotal:
        raise ValueError("Discount cannot exceed subtotal.")

    taxable_amount = subtotal - discount
    gst_amount = (taxable_amount * gst_percent / Decimal("100")).quantize(Decimal("0.01"))
    total = taxable_amount + gst_amount
    amount_paid = _money(request.form.get("amount_paid") or total)

    sale = Sale(
        invoice_number=_next_invoice_number(),
        customer=customer,
        customer_name=customer_name,
        customer_phone=customer_phone,
        subtotal=subtotal,
        discount_amount=discount,
        gst_percent=gst_percent,
        gst_amount=gst_amount,
        total_amount=total,
        amount_paid=amount_paid,
        payment_method=payment_method,
    )
    db.session.add(sale)
    db.session.flush()

    for product, quantity, line_total in cart_items:
        product.quantity -= quantity
        sale.items.append(
            SaleItem(
                product=product,
                product_name=product.name,
                quantity=quantity,
                unit_price=product.selling_price,
                line_total=line_total,
            )
        )

    db.session.commit()
    sync_products_to_excel(current_app.config["PRODUCTS_EXCEL"])
    sync_sales_to_excel(current_app.config["SALES_EXCEL"])
    return sale


@sales_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        try:
            sale = _create_sale()
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "warning")
        except Exception:
            db.session.rollback()
            flash("Unable to create invoice. Please review the cart and try again.", "danger")
        else:
            flash(f"Invoice {sale.invoice_number} created successfully.", "success")
            return redirect(url_for("sales.invoice", sale_id=sale.id))

    products = Product.query.filter(Product.quantity > 0).order_by(Product.name.asc()).all()
    customers = Customer.query.order_by(Customer.name.asc()).all()
    sales = Sale.query.order_by(Sale.created_at.desc()).limit(25).all()
    chart_labels, chart_values = _sales_chart()
    return render_template(
        "sales.html",
        title="Billing",
        products=products,
        customers=customers,
        sales=sales,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@sales_bp.route("/<int:sale_id>/invoice")
@login_required
def invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template("invoice.html", title=f"Invoice {sale.invoice_number}", sale=sale)


@sales_bp.route("/<int:sale_id>/print")
@login_required
def print_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    response = make_response(render_template("invoice.html", title=f"Invoice {sale.invoice_number}", sale=sale, auto_print=True))
    return response


@sales_bp.route("/<int:sale_id>/pdf")
@login_required
def download_pdf(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("QuickBasket AI", styles["Title"]),
        Paragraph("Smart Inventory & Sales Management System", styles["Normal"]),
        Spacer(1, 16),
        Paragraph(f"Invoice: {sale.invoice_number}", styles["Heading2"]),
        Paragraph(f"Customer: {sale.customer_name}", styles["Normal"]),
        Paragraph(f"Date: {sale.created_at.strftime('%d %b %Y, %I:%M %p')}", styles["Normal"]),
        Spacer(1, 14),
    ]

    table_data = [["Product", "Qty", "Price", "Total"]]
    for item in sale.items:
        table_data.append([
            item.product_name,
            item.quantity,
            f"Rs. {float(item.unit_price):.2f}",
            f"Rs. {float(item.line_total):.2f}",
        ])
    table_data.extend(
        [
            ["", "", "Subtotal", f"Rs. {float(sale.subtotal):.2f}"],
            ["", "", "Discount", f"Rs. {float(sale.discount_amount):.2f}"],
            ["", "", f"GST ({float(sale.gst_percent):.2f}%)", f"Rs. {float(sale.gst_amount):.2f}"],
            ["", "", "Total", f"Rs. {float(sale.total_amount):.2f}"],
        ]
    )
    table = Table(table_data, colWidths=[230, 60, 90, 90])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#101828")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)
    document.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{sale.invoice_number}.pdf",
        mimetype="application/pdf",
    )
