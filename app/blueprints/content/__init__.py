from flask import Blueprint
content_bp = Blueprint('content', __name__)
from . import routes  # noqa: E402, F401
