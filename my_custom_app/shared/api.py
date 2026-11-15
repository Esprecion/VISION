import frappe


@frappe.whitelist()
def get_my_roles():
	return {
		"user": frappe.session.user,
		"roles": frappe.get_roles(frappe.session.user),
	}


@frappe.whitelist()
def can_create(doctype):
	return bool(frappe.has_permission(doctype, "create"))


@frappe.whitelist()
def get_perms(doctype):
	return {p: bool(frappe.has_permission(doctype, p)) for p in ("create", "write", "delete")}


MODULE_DOCTYPES = {
	"business_dev": "Deal",
	"finance": "Invoice",
	"operations": "Project",
}


@frappe.whitelist()
def get_module_perms():
	"""Return read/write access for each top-level module."""
	return {
		module: {
			"read": bool(frappe.has_permission(doctype, "read")),
			"write": bool(frappe.has_permission(doctype, "write")),
		}
		for module, doctype in MODULE_DOCTYPES.items()
	}


@frappe.whitelist()
def get_module_write_perms():
	return {doctype: bool(frappe.has_permission(doctype, "write")) for doctype in MODULE_DOCTYPES.values()}
