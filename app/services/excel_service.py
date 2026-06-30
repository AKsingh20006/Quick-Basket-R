import os

from openpyxl import Workbook

from app.models import Product, Sale


PRODUCT_HEADERS = [
    "ID",
    "Name",
    "Barcode",
    "Category",
    "Quantity",
    "Low Stock Threshold",
    "Buying Price",
    "Selling Price",
    "Profit",
    "Expiry Date",
    "Supplier",
    "Image",
]

SALES_HEADERS = [
    "Invoice",
    "Date",
    "Customer",
    "Phone",
    "Items",
    "Subtotal",
    "Discount",
    "GST %",
    "GST Amount",
    "Total",
    "Paid",
    "Payment Method",
]


def sync_products_to_excel(excel_path):
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Products"
    worksheet.append(PRODUCT_HEADERS)

    products = Product.query.order_by(Product.id.asc()).all()
    for product in products:
        worksheet.append(
            [
                product.id,
                product.name,
                product.barcode,
                product.category,
                product.quantity,
                product.low_stock_threshold,
                float(product.buying_price or 0),
                float(product.selling_price or 0),
                product.profit,
                product.expiry_date.isoformat() if product.expiry_date else "",
                product.supplier,
                product.image_filename,
            ]
        )

    for column_cells in worksheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 28)

    workbook.save(excel_path)


def sync_sales_to_excel(excel_path):
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sales"
    worksheet.append(SALES_HEADERS)

    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    for sale in sales:
        items = ", ".join(f"{item.product_name} x {item.quantity}" for item in sale.items)
        worksheet.append(
            [
                sale.invoice_number,
                sale.created_at.strftime("%Y-%m-%d %H:%M"),
                sale.customer_name,
                sale.customer_phone,
                items,
                float(sale.subtotal or 0),
                float(sale.discount_amount or 0),
                float(sale.gst_percent or 0),
                float(sale.gst_amount or 0),
                float(sale.total_amount or 0),
                float(sale.amount_paid or 0),
                sale.payment_method,
            ]
        )

    for column_cells in worksheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 36)

    workbook.save(excel_path)
