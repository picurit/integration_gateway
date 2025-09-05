import frappe
import json
from frappe.model.document import Document
from frappe.integrations.doctype.webhook.webhook import Webhook, get_context
from integration_gateway.utils import TemplateDocProxy

def get_webhook_data(doc: Document, webhook: Webhook) -> dict:
    data = {}
    doc_dict = doc.as_dict(convert_dates_to_str=True)

    proxy = TemplateDocProxy(doc, doc_dict)

    if webhook.webhook_data:
        data = {w.key: doc_dict.get(w.fieldname) for w in webhook.webhook_data}
    elif webhook.webhook_json:
        rendered = frappe.render_template(webhook.webhook_json, get_context(proxy))
        # rendered should be a JSON string; parse it
        data = json.loads(rendered) if rendered else {}

    return data