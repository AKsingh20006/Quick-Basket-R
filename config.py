import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "quickbasket-ai-secret")

    DATABASE_URL = os.getenv("DATABASE_URL")

    DB_PATH = os.path.join(INSTANCE_DIR, "inventory.db")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///" +
            DB_PATH
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PRODUCTS_EXCEL = os.path.join(
        BASE_DIR,
        "excel",
        "products.xlsx"
    )

    SALES_EXCEL = os.path.join(
        BASE_DIR,
        "excel",
        "sales.xlsx"
    )

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "app",
        "static",
        "img",
        "products"
    )

    BACKUP_FOLDER = os.path.join(
        INSTANCE_DIR,
        "backups"
    )

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024