from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    EmailField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = EmailField(
        "Email address",
        validators=[DataRequired(), Email(), Length(max=255)],
        render_kw={"autocomplete": "email"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
        render_kw={"autocomplete": "current-password"},
    )
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class RegistrationForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=120)],
        render_kw={"autocomplete": "name"},
    )
    email = EmailField(
        "Email address",
        validators=[DataRequired(), Email(), Length(max=255)],
        render_kw={"autocomplete": "email"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Create account")


class ProductForm(FlaskForm):
    name = StringField(
        "Product name",
        validators=[DataRequired(), Length(min=2, max=160)],
    )
    barcode = StringField(
        "Barcode",
        validators=[Optional(), Length(max=80)],
    )
    category = StringField(
        "Category",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    quantity = IntegerField(
        "Quantity",
        validators=[DataRequired(), NumberRange(min=0)],
        default=0,
    )
    low_stock_threshold = IntegerField(
        "Low stock alert",
        validators=[DataRequired(), NumberRange(min=0)],
        default=10,
    )
    buying_price = DecimalField(
        "Buying price",
        validators=[DataRequired(), NumberRange(min=0)],
        places=2,
        default=0,
    )
    selling_price = DecimalField(
        "Selling price",
        validators=[DataRequired(), NumberRange(min=0)],
        places=2,
        default=0,
    )
    expiry_date = DateField(
        "Expiry date",
        validators=[Optional()],
        format="%Y-%m-%d",
    )
    supplier = StringField(
        "Supplier",
        validators=[Optional(), Length(max=160)],
    )
    image = FileField(
        "Product image",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Upload JPG, PNG, or WEBP images only."),
        ],
    )
    submit = SubmitField("Save product")
