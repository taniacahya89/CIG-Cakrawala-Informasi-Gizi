"""Auth forms — Registration, Login, Password Reset."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User


# Age range options
AGE_RANGE_CHOICES = [
    ('', 'Pilih rentang usia'),
    ('13-17', '13 - 17 tahun'),
    ('18-25', '18 - 25 tahun'),
    ('26-35', '26 - 35 tahun'),
    ('36-45', '36 - 45 tahun'),
    ('46-55', '46 - 55 tahun'),
    ('56+', '56 tahun ke atas'),
]


class RegistrationForm(FlaskForm):
    """User registration form."""

    full_name = StringField('Nama Lengkap', validators=[
        DataRequired(message='Nama lengkap wajib diisi.'),
        Length(min=2, max=150, message='Nama harus antara 2-150 karakter.'),
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email wajib diisi.'),
        Email(message='Format email tidak valid.'),
        Length(max=255),
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
        Length(max=100, message='Nama kota maksimal 100 karakter.'),
    ])
    submit = SubmitField('Daftar')

    def validate_email(self, field):
        """Check if email is already registered."""
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('Email sudah terdaftar. Silakan gunakan email lain.')


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField('Email', validators=[
        DataRequired(message='Email wajib diisi.'),
        Email(message='Format email tidak valid.'),
    ])
    password = PasswordField('Kata Sandi', validators=[
        DataRequired(message='Kata sandi wajib diisi.'),
    ])
    remember = BooleanField('Ingat Saya')
    submit = SubmitField('Masuk')


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""

    email = StringField('Email', validators=[
        DataRequired(message='Email wajib diisi.'),
        Email(message='Format email tidak valid.'),
    ])
    submit = SubmitField('Kirim Tautan Reset')


class ResetPasswordForm(FlaskForm):
    """Reset password form."""

    password = PasswordField('Kata Sandi Baru', validators=[
        DataRequired(message='Kata sandi baru wajib diisi.'),
        Length(min=8, message='Kata sandi minimal 8 karakter.'),
    ])
    password_confirm = PasswordField('Konfirmasi Kata Sandi Baru', validators=[
        DataRequired(message='Konfirmasi kata sandi wajib diisi.'),
        EqualTo('password', message='Kata sandi tidak cocok.'),
    ])
    submit = SubmitField('Atur Ulang Kata Sandi')
