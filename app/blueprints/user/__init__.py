"""User blueprint — Dashboard and Profile Management."""

from flask import Blueprint

user_bp = Blueprint('user', __name__, template_folder='../../templates/user')

from . import routes  # noqa: E402, F401
