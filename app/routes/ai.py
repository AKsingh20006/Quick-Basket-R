from flask import Blueprint, render_template
from flask_login import login_required

from app.services.ai_service import build_ai_report

ai_bp = Blueprint("ai", __name__, url_prefix="/ai-insights")


@ai_bp.route("/")
@login_required
def index():
    return render_template("ai_insights.html", title="AI Insights", report=build_ai_report())
