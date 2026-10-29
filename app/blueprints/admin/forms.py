"""Admin forms — Invitation management."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from app.blueprints.auth.forms import AGE_RANGE_CHOICES


class AdminInviteForm(FlaskForm):
    """Form to invite a new administrator."""

    email = StringField('Email', validators=[
        DataRequired(message='Email wajib diisi.'),
        Email(message='Format email tidak valid.'),
        Length(max=255),
    ])
    submit = SubmitField('Kirim Undangan')


class AcceptInviteForm(FlaskForm):
    """Form to accept an admin invitation and create account."""

    full_name = StringField('Nama Lengkap', validators=[
        DataRequired(message='Nama lengkap wajib diisi.'),
        Length(min=2, max=150, message='Nama harus antara 2-150 karakter.'),
    ])
    password = PasswordField('Kata Sandi', validators=[
        DataRequired(message='Kata sandi wajib diisi.'),
        Length(min=8, message='Kata sandi minimal 8 karakter.'),
    ])
    password_confirm = PasswordField('Konfirmasi Kata Sandi', validators=[
        DataRequired(message='Konfirmasi kata sandi wajib diisi.'),
        EqualTo('password', message='Kata sandi tidak cocok.'),
    ])
    age_range = SelectField('Rentang Usia', choices=AGE_RANGE_CHOICES, validators=[
        DataRequired(message='Rentang usia wajib dipilih.'),
    ])
    city = StringField('Kota/Kabupaten', validators=[
        DataRequired(message='Kota/kabupaten wajib diisi.'),
        Length(max=100),
    ])
    submit = SubmitField('Terima Undangan & Buat Akun')
