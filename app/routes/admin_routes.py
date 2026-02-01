# Deprecated: Moved to app/routes/admin/
# This shim exists for backward compatibility during transition
from app.routes.admin import admin_bp
from app.decorators import login_required, admin_required
