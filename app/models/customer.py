from datetime import datetime, timezone

from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True, index=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    sales = db.relationship("Sale", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name}>"
