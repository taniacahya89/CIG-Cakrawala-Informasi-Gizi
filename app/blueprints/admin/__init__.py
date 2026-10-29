"""Admin blueprint — Administrator dashboard and invitations."""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='../../templates/admin')

from . import routes  # noqa: E402, F401
from . import content_routes  # noqa: E402, F401
