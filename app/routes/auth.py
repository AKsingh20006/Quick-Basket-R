from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegistrationForm
from app.models import User

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
)


def _is_safe_next_url(target):
    if not target:
        return False

    current_host = urlsplit(request.host_url).netloc
    target_host = urlsplit(target).netloc
    return not target_host or target_host == current_host


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account is inactive. Please contact an administrator.", "warning")
                return redirect(url_for("auth.login"))

            login_user(user, remember=form.remember.data)
            flash("Welcome back.", "success")

            next_url = request.args.get("next")
            if _is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form, title="Sign in")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with that email already exists.", "warning")
            return redirect(url_for("auth.register"))

        user = User(name=form.name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Your QuickBasket AI account is ready.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html", form=form, title="Create account")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
