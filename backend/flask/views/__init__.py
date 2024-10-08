from flask import Blueprint

library_manage_blueprint = Blueprint('library_manage', __name__)

from . import views
