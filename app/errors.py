from flask import render_template
from flask_wtf.csrf import CSRFError

from app.extensions import db


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/error.html", title="Forbidden", code=403,
                                message="You don't have permission to access this page."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/error.html", title="Not Found", code=404,
                                message="The page you are looking for could not be found."), 404

    @app.errorhandler(413)
    def too_large_error(error):
        return render_template("errors/error.html", title="File Too Large", code=413,
                                message="The uploaded file is too large."), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/error.html", title="Server Error", code=500,
                                message="Something went wrong on our end. Please try again."), 500

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("errors/error.html", title="Session Expired", code=400,
                                message="Your form session has expired. Please try again."), 400
