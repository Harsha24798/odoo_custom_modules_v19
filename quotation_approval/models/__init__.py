# Import all model files so Odoo can find them

# This imports our settings model
from . import res_config_settings
# ↑ Loads: models/res_config_settings.py

# This imports our quotation approval logic
from . import sale_order
# ↑ Loads: models/sale_order.py

# Now when Odoo loads this module, it knows about:
# 1. ResConfigSettings - for storing approval settings
# 2. SaleOrder - for approval logic on quotations
