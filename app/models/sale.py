from datetime import datetime, timezone

from app.extensions import db


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(160), nullable=False, default="Walk-in Customer")
    customer_phone = db.Column(db.String(30), nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    gst_percent = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    gst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(40), nullable=False, default="Cash")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    customer = db.relationship("Customer", back_populates="sales")
    items = db.relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        order_by="SaleItem.id",
    )

    @property
    def balance(self):
        return float(self.amount_paid or 0) - float(self.total_amount or 0)

    def __repr__(self):
        return f"<Sale {self.invoice_number}>"


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(160), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<SaleItem {self.product_name} x {self.quantity}>"
