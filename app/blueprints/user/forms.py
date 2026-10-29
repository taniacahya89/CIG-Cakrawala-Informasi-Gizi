"""User profile forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from flask_login import current_user
from app.models.user import User
from app.blueprints.auth.forms import AGE_RANGE_CHOICES


class ProfileForm(FlaskForm):
    """User profile update form."""

    full_name = StringField('Nama Lengkap', validators=[
        DataRequired(message='Nama lengkap wajib diisi.'),
        Length(min=2, max=150, message='Nama harus antara 2-150 karakter.'),
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email wajib diisi.'),
        Email(message='Format email tidak valid.'),
        Length(max=255),
    ])
    age_range = SelectField('Rentang Usia', choices=AGE_RANGE_CHOICES, validators=[
        DataRequired(message='Rentang usia wajib dipilih.'),
    ])
    city = StringField('Kota/Kabupaten', validators=[
        DataRequired(message='Kota/kabupaten wajib diisi.'),
        Length(max=100),
    ])
    password_verification = PasswordField('Kata Sandi Saat Ini (Diperlukan jika mengubah email)', validators=[
        Optional(),
    ])
    submit = SubmitField('Simpan Perubahan')

    def validate_email(self, field):
        """Check if email is already taken by another user."""
        if field.data.lower().strip() != current_user.email:
            if User.query.filter_by(email=field.data.lower().strip()).first():
                raise ValidationError('Email sudah digunakan oleh akun lain.')


class ChangePasswordForm(FlaskForm):
    """Change password form — requires current password verification."""

    current_password = PasswordField('Kata Sandi Saat Ini', validators=[
        DataRequired(message='Kata sandi saat ini wajib diisi.'),
    ])
    new_password = PasswordField('Kata Sandi Baru', validators=[
        DataRequired(message='Kata sandi baru wajib diisi.'),
        Length(min=8, message='Kata sandi minimal 8 karakter.'),
    ])
    new_password_confirm = PasswordField('Konfirmasi Kata Sandi Baru', validators=[
        DataRequired(message='Konfirmasi kata sandi wajib diisi.'),
        EqualTo('new_password', message='Kata sandi tidak cocok.'),
    ])
    submit = SubmitField('Ubah Kata Sandi')
