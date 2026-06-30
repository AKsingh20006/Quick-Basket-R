from datetime import datetime, timezone

from app.extensions import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def product_count(self):
        from app.models.product import Product

        return Product.query.filter(Product.supplier == self.name).count()

    def __repr__(self):
        return f"<Supplier {self.name}>"
