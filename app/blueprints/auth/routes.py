"""Auth blueprint routes — Login, Register, Password Reset."""

from urllib.parse import urlparse
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter
from app.models.user import User
from app.utils.tokens import (
    create_password_reset_token,
    verify_password_reset_token,
    consume_password_reset_token,
)
from app.utils.email import send_password_reset_email
from .forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from . import auth_bp


def is_safe_url(target):
    """Validate that a redirect URL is safe (same host)."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return (
        test_url.scheme in ('', 'http', 'https')
        and ref_url.netloc == test_url.netloc
    )


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            age_range=form.age_range.data,
            city=form.city.data.strip(),
            role='user',  # Always assign standard user role
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Pendaftaran berhasil! Silakan masuk dengan akun Anda.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    """User login."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash('Email atau kata sandi salah.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_active:
            flash('Akun Anda telah dinonaktifkan. Hubungi administrator.', 'danger')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=form.remember.data)

        # Safe redirect after login
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout (POST only with CSRF protection)."""
    logout_user()
    flash('Anda telah berhasil keluar.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('3 per hour')
def forgot_password():
    """Request a password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user:
            token = create_password_reset_token(user)
            base_url = request.host_url.rstrip('/')
            email_sent = send_password_reset_email(user, token, base_url)

            # Keep response identical regardless of account and mail delivery status.
            if not email_sent:
                import logging
                logging.getLogger(__name__).warning('Reset email could not be delivered; check local mail configuration.')
            flash('Jika email terdaftar, instruksi reset akan dikirim.', 'info')
        else:
            # Don't reveal whether the email exists
            flash('Jika email terdaftar, tautan reset akan dikirim.', 'info')

        return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using a valid token."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    user = verify_password_reset_token(token)
    if user is None:
        flash('Tautan reset tidak valid atau sudah kedaluwarsa.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        consume_password_reset_token(token)
        db.session.commit()

        flash('Kata sandi berhasil diubah. Silakan masuk dengan kata sandi baru.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)
