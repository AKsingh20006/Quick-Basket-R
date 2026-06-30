from datetime import date, timedelta

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import inspect, text

from app.extensions import db
from app.services.ai_service import ai_dashboard_summary

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
)


def _table_exists(table_name):
    return inspect(db.engine).has_table(table_name)


def _scalar(query, params=None, default=0):
    try:
        value = db.session.execute(text(query), params or {}).scalar()
    except Exception:
        db.session.rollback()
        return default
    return value if value is not None else default


def _rows(query, params=None):
    try:
        return db.session.execute(text(query), params or {}).mappings().all()
    except Exception:
        db.session.rollback()
        return []


def _dashboard_metrics():
    today = date.today()
    labels = [(today - timedelta(days=offset)).strftime("%d %b") for offset in range(6, -1, -1)]
    metrics = {
        "total_products": 0,
        "low_stock": 0,
        "todays_sales": 0,
        "revenue": 0,
        "recent_products": [],
        "low_stock_products": [],
        "sales_labels": labels,
        "sales_values": [0 for _ in labels],
    }

    if _table_exists("products"):
        metrics["total_products"] = _scalar("SELECT COUNT(*) FROM products")
        metrics["low_stock"] = _scalar(
            """
            SELECT COUNT(*)
            FROM products
            WHERE quantity <= low_stock_threshold
            """
        )
        metrics["recent_products"] = _rows(
            """
            SELECT id, name, category, quantity AS stock, selling_price AS price
            FROM products
            ORDER BY id DESC
            LIMIT 5
            """
        )
        metrics["low_stock_products"] = _rows(
            """
            SELECT id, name, quantity AS stock, low_stock_threshold AS threshold
            FROM products
            WHERE quantity <= low_stock_threshold
            ORDER BY quantity ASC
            LIMIT 5
            """
        )

    if _table_exists("sales"):
        metrics["todays_sales"] = _scalar(
            "SELECT COUNT(*) FROM sales WHERE DATE(created_at) = :today",
            {"today": today.isoformat()},
        )
        metrics["revenue"] = float(
            _scalar(
                "SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE DATE(created_at) = :today",
                {"today": today.isoformat()},
            )
        )
        sales_rows = _rows(
            """
            SELECT DATE(created_at) AS sale_date, COALESCE(SUM(total_amount), 0) AS revenue
            FROM sales
            WHERE DATE(created_at) >= :start_date
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
            """,
            {"start_date": (today - timedelta(days=6)).isoformat()},
        )
        sales_by_date = {row["sale_date"]: float(row["revenue"]) for row in sales_rows}
        metrics["sales_values"] = [
            sales_by_date.get((today - timedelta(days=offset)).isoformat(), 0)
            for offset in range(6, -1, -1)
        ]

    return metrics


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    return render_template(
        "dashboard.html",
        title="Dashboard",
        metrics=_dashboard_metrics(),
        ai_summary=ai_dashboard_summary(),
    )
