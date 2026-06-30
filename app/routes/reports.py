import csv
from datetime import date
from io import BytesIO, StringIO

from flask import Blueprint, Response, render_template, request, send_file
from flask_login import login_required
from openpyxl import Workbook
from sqlalchemy import func

from app.extensions import db
from app.models import Product, Sale, SaleItem

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _money(value):
    return float(value or 0)


def _revenue_summary():
    today = date.today()
    total_revenue = _money(db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).scalar())
    today_revenue = _money(
        db.session.query(func.coalesce(func.sum(Sale.total_amount), 0))
        .filter(func.date(Sale.created_at) == today.isoformat())
        .scalar()
    )
    total_sales = Sale.query.count()
    average_invoice = total_revenue / total_sales if total_sales else 0
    return {
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "total_sales": total_sales,
        "average_invoice": average_invoice,
    }


def _monthly_sales_chart():
    rows = (
        db.session.query(
            func.strftime("%Y-%m", Sale.created_at).label("month"),
            func.coalesce(func.sum(Sale.total_amount), 0).label("revenue"),
        )
        .group_by("month")
        .order_by("month")
        .limit(12)
        .all()
    )
    return {
        "labels": [row.month for row in rows],
        "values": [_money(row.revenue) for row in rows],
    }


def _top_selling_products(limit=8):
    rows = (
        db.session.query(
            SaleItem.product_name,
            func.coalesce(func.sum(SaleItem.quantity), 0).label("quantity_sold"),
            func.coalesce(func.sum(SaleItem.line_total), 0).label("revenue"),
        )
        .group_by(SaleItem.product_name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "name": row.product_name,
            "quantity_sold": int(row.quantity_sold or 0),
            "revenue": _money(row.revenue),
        }
        for row in rows
    ]


def _sales_rows():
    return Sale.query.order_by(Sale.created_at.desc()).all()


def _inventory_rows():
    return Product.query.order_by(Product.name.asc()).all()


def _low_stock_rows():
    return (
        Product.query.filter(Product.quantity <= Product.low_stock_threshold)
        .order_by(Product.quantity.asc(), Product.name.asc())
        .all()
    )


def _csv_response(filename, headers, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _excel_response(filename, sheet_name, headers, rows):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)

    for column_cells in worksheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 36)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _sales_export_rows():
    rows = []
    for sale in _sales_rows():
        rows.append(
            [
                sale.invoice_number,
                sale.created_at.strftime("%Y-%m-%d %H:%M"),
                sale.customer_name,
                sale.customer_phone or "",
                len(sale.items),
                _money(sale.subtotal),
                _money(sale.discount_amount),
                _money(sale.gst_amount),
                _money(sale.total_amount),
                sale.payment_method,
            ]
        )
    return rows


def _inventory_export_rows():
    rows = []
    for product in _inventory_rows():
        rows.append(
            [
                product.name,
                product.barcode or "",
                product.category,
                product.quantity,
                product.low_stock_threshold,
                _money(product.buying_price),
                _money(product.selling_price),
                product.profit,
                product.expiry_date.isoformat() if product.expiry_date else "",
                product.supplier or "",
                product.stock_status,
            ]
        )
    return rows


def _handle_export(report_type):
    export_type = request.args.get("export")
    if not export_type:
        return None

    if report_type == "sales":
        headers = [
            "Invoice",
            "Date",
            "Customer",
            "Phone",
            "Items",
            "Subtotal",
            "Discount",
            "GST",
            "Total",
            "Payment Method",
        ]
        rows = _sales_export_rows()
        filename_base = "sales-report"
        sheet_name = "Sales Report"
    else:
        headers = [
            "Product",
            "Barcode",
            "Category",
            "Quantity",
            "Low Stock Threshold",
            "Buying Price",
            "Selling Price",
            "Profit",
            "Expiry Date",
            "Supplier",
            "Stock Status",
        ]
        rows = _inventory_export_rows()
        filename_base = "inventory-report"
        sheet_name = "Inventory Report"

    if export_type == "csv":
        return _csv_response(f"{filename_base}.csv", headers, rows)
    if export_type == "excel":
        return _excel_response(f"{filename_base}.xlsx", sheet_name, headers, rows)
    return None


def _report_context(report_type):
    return {
        "report_type": report_type,
        "summary": _revenue_summary(),
        "monthly_chart": _monthly_sales_chart(),
        "top_products": _top_selling_products(),
        "sales": _sales_rows(),
        "inventory": _inventory_rows(),
        "low_stock": _low_stock_rows(),
    }


@reports_bp.route("/")
@login_required
def index():
    return render_template("reports.html", title="Reports", **_report_context("overview"))


@reports_bp.route("/sales")
@login_required
def sales_report():
    export_response = _handle_export("sales")
    if export_response:
        return export_response
    return render_template("reports.html", title="Sales Report", **_report_context("sales"))


@reports_bp.route("/inventory")
@login_required
def inventory_report():
    export_response = _handle_export("inventory")
    if export_response:
        return export_response
    return render_template("reports.html", title="Inventory Report", **_report_context("inventory"))
