from datetime import datetime, timezone

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    barcode = db.Column(db.String(80), unique=True, nullable=True, index=True)
    category = db.Column(db.String(100), nullable=False, default="General", index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=10)
    buying_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=True)
    supplier = db.Column(db.String(160), nullable=True, index=True)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def profit(self):
        return float(self.selling_price or 0) - float(self.buying_price or 0)

    @property
    def stock_status(self):
        if self.quantity <= 0:
            return "Out of stock"
        if self.quantity <= self.low_stock_threshold:
            return "Low stock"
        return "In stock"

    def __repr__(self):
        return f"<Product {self.name}>"
