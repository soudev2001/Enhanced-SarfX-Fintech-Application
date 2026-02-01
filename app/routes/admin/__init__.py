from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import all route modules to register their routes on admin_bp
from . import dashboard
from . import user_management
from . import wallet_management
from . import transaction_management
from . import beneficiary_management
from . import atm_management
from . import source_management
from . import demo_management
