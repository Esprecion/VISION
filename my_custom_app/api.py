import frappe


@frappe.whitelist()
def get_my_roles():
    return {
        "user": frappe.session.user,
        "roles": frappe.get_roles(frappe.session.user),
    }
