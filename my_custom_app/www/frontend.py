import frappe

no_cache = 1

def get_context():
    context = frappe._dict()
    context.boot = frappe._dict({
        "csrf_token": frappe.sessions.get_csrf_token(),
        "site_name": frappe.local.site,
    })
    return context
