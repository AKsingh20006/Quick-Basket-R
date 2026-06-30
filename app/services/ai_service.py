import base64
from datetime import date, timedelta
from io import BytesIO

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import func

from app.extensions import db
from app.models import Product, Sale, SaleItem


def _chart_to_base64():
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
    plt.close()
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _daily_sales(days=30):
    start_date = date.today() - timedelta(days=days - 1)
    rows = (
        db.session.query(func.date(Sale.created_at), func.coalesce(func.sum(Sale.total_amount), 0))
        .filter(func.date(Sale.created_at) >= start_date.isoformat())
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at))
        .all()
    )
    values_by_date = {row[0]: float(row[1] or 0) for row in rows}
    labels = [(start_date + timedelta(days=offset)).isoformat() for offset in range(days)]
    values = [values_by_date.get(day, 0) for day in labels]
    return labels, values


def predict_sales(days_ahead=7):
    labels, values = _daily_sales(days=30)
    non_zero_days = sum(1 for value in values if value > 0)
    if non_zero_days < 2:
        forecast = [round(sum(values[-7:]) / 7 if values else 0, 2) for _ in range(days_ahead)]
        confidence = "Needs more sales data"
    else:
        x = np.arange(len(values)).reshape(-1, 1)
        y = np.array(values)
        model = LinearRegression()
        model.fit(x, y)
        future_x = np.arange(len(values), len(values) + days_ahead).reshape(-1, 1)
        forecast = [round(max(value, 0), 2) for value in model.predict(future_x)]
        confidence = "Linear regression forecast"

    future_labels = [(date.today() + timedelta(days=offset)).strftime("%d %b") for offset in range(1, days_ahead + 1)]

    plt.figure(figsize=(8, 3.2))
    plt.plot(labels[-14:], values[-14:], marker="o", color="#2563eb", label="Actual")
    plt.plot(future_labels, forecast, marker="o", linestyle="--", color="#059669", label="Prediction")
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Revenue")
    plt.title("Sales Prediction")
    plt.grid(axis="y", alpha=0.22)
    plt.legend()

    return {
        "labels": future_labels,
        "values": forecast,
        "next_7_days_total": round(sum(forecast), 2),
        "confidence": confidence,
        "chart": _chart_to_base64(),
    }


def top_selling_products(limit=5):
    rows = (
        db.session.query(
            SaleItem.product_id,
            SaleItem.product_name,
            func.coalesce(func.sum(SaleItem.quantity), 0).label("sold"),
            func.coalesce(func.sum(SaleItem.line_total), 0).label("revenue"),
        )
        .group_by(SaleItem.product_id, SaleItem.product_name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
        .all()
    )
    products = [
        {
            "product_id": row.product_id,
            "name": row.product_name,
            "sold": int(row.sold or 0),
            "revenue": float(row.revenue or 0),
        }
        for row in rows
    ]

    if products:
        plt.figure(figsize=(7, 3.2))
        plt.barh([product["name"] for product in reversed(products)], [product["sold"] for product in reversed(products)], color="#2563eb")
        plt.xlabel("Units sold")
        plt.title("Top Selling Products")
        plt.grid(axis="x", alpha=0.22)
        chart = _chart_to_base64()
    else:
        chart = None

    return {"products": products, "chart": chart}


def demand_forecast(limit=6):
    top = top_selling_products(limit=limit)["products"]
    forecasts = []
    for item in top:
        sold_30_days = item["sold"]
        avg_daily_demand = sold_30_days / 30
        forecasts.append(
            {
                "name": item["name"],
                "avg_daily_demand": round(avg_daily_demand, 2),
                "next_7_days": round(avg_daily_demand * 7, 2),
                "next_30_days": round(avg_daily_demand * 30, 2),
            }
        )
    return forecasts


def low_stock_prediction(limit=8):
    products = Product.query.order_by(Product.quantity.asc()).all()
    predictions = []
    for product in products:
        sold_30_days = (
            db.session.query(func.coalesce(func.sum(SaleItem.quantity), 0))
            .join(Sale)
            .filter(
                SaleItem.product_id == product.id,
                func.date(Sale.created_at) >= (date.today() - timedelta(days=29)).isoformat(),
            )
            .scalar()
            or 0
        )
        avg_daily_sales = float(sold_30_days) / 30
        if avg_daily_sales > 0:
            days_left = round(product.quantity / avg_daily_sales, 1)
        else:
            days_left = None

        risk_score = 0
        if product.quantity <= product.low_stock_threshold:
            risk_score += 60
        if days_left is not None and days_left <= 7:
            risk_score += 30
        elif days_left is not None and days_left <= 14:
            risk_score += 15

        if risk_score or len(predictions) < limit:
            predictions.append(
                {
                    "name": product.name,
                    "quantity": product.quantity,
                    "threshold": product.low_stock_threshold,
                    "avg_daily_sales": round(avg_daily_sales, 2),
                    "days_left": days_left,
                    "risk": min(risk_score, 100),
                    "label": "High" if risk_score >= 75 else "Medium" if risk_score >= 40 else "Watch",
                }
            )

    return sorted(predictions, key=lambda item: (item["risk"], -item["quantity"]), reverse=True)[:limit]


def business_insights():
    product_count = Product.query.count()
    sale_count = Sale.query.count()
    revenue = float(db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).scalar() or 0)
    low_stock_count = Product.query.filter(Product.quantity <= Product.low_stock_threshold).count()
    avg_invoice = revenue / sale_count if sale_count else 0
    top = top_selling_products(limit=1)["products"]

    insights = []
    if low_stock_count:
        insights.append(f"{low_stock_count} product(s) are at or below the low-stock threshold.")
    else:
        insights.append("Inventory stock health is stable right now.")

    if top:
        insights.append(f"{top[0]['name']} is currently the top seller with {top[0]['sold']} units sold.")
    else:
        insights.append("Start billing sales to unlock product demand insights.")

    if sale_count:
        insights.append(f"Average invoice value is Rs. {avg_invoice:.2f}.")
    else:
        insights.append("No completed sales yet, so revenue predictions are using neutral baselines.")

    if product_count and not sale_count:
        insights.append("Inventory is ready; sales history will improve AI accuracy over time.")

    return {
        "product_count": product_count,
        "sale_count": sale_count,
        "revenue": round(revenue, 2),
        "low_stock_count": low_stock_count,
        "avg_invoice": round(avg_invoice, 2),
        "insights": insights,
    }


def ai_dashboard_summary():
    sales_prediction = predict_sales(days_ahead=7)
    low_stock = low_stock_prediction(limit=3)
    top = top_selling_products(limit=3)["products"]
    insights = business_insights()["insights"][:2]
    return {
        "predicted_revenue": sales_prediction["next_7_days_total"],
        "low_stock_predictions": low_stock,
        "top_products": top,
        "insights": insights,
    }


def build_ai_report():
    return {
        "sales_prediction": predict_sales(),
        "top_selling": top_selling_products(),
        "demand_forecast": demand_forecast(),
        "low_stock_prediction": low_stock_prediction(),
        "business": business_insights(),
    }
