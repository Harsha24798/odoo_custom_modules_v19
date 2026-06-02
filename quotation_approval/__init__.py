# This file tells Python: "This folder is a package"
# Without this file, Python won't treat the folder as a package

# Import the models module so Odoo can load our Python models
from . import models
# ↑ The dot (.) means "from the current package"
# ↑ So this loads: quotation_approval/models/__init__.py
# ↑ Which in turn loads all model files
