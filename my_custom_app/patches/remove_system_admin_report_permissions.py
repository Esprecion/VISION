import frappe

MODULES = ("Business Development", "Finance", "Operations")


def execute():
	for report in frappe.get_all("Report", filters={"module": ("in", MODULES)}, pluck="name"):
		doc = frappe.get_doc("Report", report)
		remaining = [row for row in doc.roles if row.role != "System Admin"]
		if len(remaining) != len(doc.roles):
			doc.set("roles", remaining)
			doc.save(ignore_permissions=True)
