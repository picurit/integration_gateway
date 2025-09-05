__version__ = "0.0.1"

# Monkey Patching overrides for standard Frappe Doctypes

from frappe.integrations.doctype.webhook import webhook
from integration_gateway.overrides.webhook.custom_webhook import get_webhook_data as custom_get_webhook_data

webhook.get_webhook_data = custom_get_webhook_data