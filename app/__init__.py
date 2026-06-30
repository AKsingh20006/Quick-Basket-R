import os

from flask import Flask

from config import Config
from app.extensions import csrf, db, login_manager, migrate


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["BACKUP_FOLDER"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["PRODUCTS_EXCEL"]), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales import sales_bp
    from app.routes.customers import customers_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.reports import reports_bp
    from app.routes.ai import ai_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(settings_bp)

    from app.errors import register_error_handlers

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
