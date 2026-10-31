"""Email utility for CIG.

Email tokens are never printed to the console.
For local SMTP testing, a tool such as MailHog can be configured separately.
"""

from html import escape
from flask import current_app
from flask_mail import Message
from app.extensions import mail


def send_email(to, subject, body_text, body_html=None):
    """Send an email message.

    If delivery fails, log only a generic warning (never access tokens).
    """
    msg = Message(
        subject=subject,
        recipients=[to] if isinstance(to, str) else to,
        body=body_text,
        html=body_html,
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        # In development, log the email instead of failing
        current_app.logger.warning(f'Email delivery failed: {e}')
        return False


def send_password_reset_email(user, token, base_url):
    """Send a password reset email to the user."""
    reset_url = f'{base_url}/auth/reset-password/{token}'

    subject = 'CIG — Atur Ulang Kata Sandi'
    body_text = f"""Halo {user.full_name},

Kami menerima permintaan untuk mengatur ulang kata sandi akun CIG Anda.

Klik tautan berikut untuk mengatur ulang kata sandi Anda:
{reset_url}

Tautan ini berlaku selama 1 jam.

Jika Anda tidak meminta pengaturan ulang kata sandi, abaikan email ini.

Salam,
Tim Cakrawala Informasi Gizi
"""

    safe_name = escape(user.full_name)
    safe_reset_url = escape(reset_url, quote=True)
    body_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #C62828;">Atur Ulang Kata Sandi</h2>
        <p>Halo <strong>{safe_name}</strong>,</p>
        <p>Kami menerima permintaan untuk mengatur ulang kata sandi akun CIG Anda.</p>
        <p>
            <a href="{safe_reset_url}"
               style="display: inline-block; padding: 12px 24px; background-color: #C62828;
                      color: white; text-decoration: none; border-radius: 9999px;">
                Atur Ulang Kata Sandi
            </a>
        </p>
        <p style="color: #666;">Tautan ini berlaku selama 1 jam.</p>
        <p style="color: #666;">Jika Anda tidak meminta pengaturan ulang kata sandi, abaikan email ini.</p>
        <hr style="border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">Tim Cakrawala Informasi Gizi</p>
    </div>
    """

    return send_email(user.email, subject, body_text, body_html)


def send_admin_invitation_email(email, token, invited_by, base_url):
    """Send an admin invitation email."""
    invite_url = f'{base_url}/admin/accept-invite/{token}'

    subject = 'CIG — Undangan Administrator'
    body_text = f"""Halo,

Anda diundang oleh {invited_by.full_name} untuk menjadi administrator Cakrawala Informasi Gizi (CIG).

Klik tautan berikut untuk menerima undangan:
{invite_url}

Tautan ini berlaku selama 24 jam.

Jika Anda tidak mengenal pengirim undangan ini, abaikan email ini.

Salam,
Tim Cakrawala Informasi Gizi
"""

    safe_inviter_name = escape(invited_by.full_name)
    safe_invite_url = escape(invite_url, quote=True)
    body_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1B5E20;">Undangan Administrator CIG</h2>
        <p>Halo,</p>
        <p>Anda diundang oleh <strong>{safe_inviter_name}</strong> untuk menjadi administrator
           <strong>Cakrawala Informasi Gizi (CIG)</strong>.</p>
        <p>
            <a href="{safe_invite_url}"
               style="display: inline-block; padding: 12px 24px; background-color: #1B5E20;
                      color: white; text-decoration: none; border-radius: 9999px;">
                Terima Undangan
            </a>
        </p>
        <p style="color: #666;">Tautan ini berlaku selama 24 jam.</p>
        <p style="color: #666;">Jika Anda tidak mengenal pengirim undangan ini, abaikan email ini.</p>
        <hr style="border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">Tim Cakrawala Informasi Gizi</p>
    </div>
    """

    return send_email(email, subject, body_text, body_html)
